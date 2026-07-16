import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import apply_rate_limit, rate_limiter
from app.core.sanitize import ensure_present, sanitize_text
from app.db.session import get_db
from app.models.user import User
from app.repositories.conversation import ConversationRepository
from app.repositories.document import DocumentRepository
from app.repositories.message import MessageRepository
from app.schemas.assistant import (
    AnalyticsOverview,
    AssistantQuizResponse,
    AssistantSummaryRequest,
    AssistantSummaryResponse,
    DashboardSummary,
    SemanticDocumentSearchItem,
    SemanticDocumentSearchResponse,
    SuggestedPromptsResponse,
    StudyNotesRequest,
    StudyNotesResponse,
)
from app.schemas.rag import AssistantQueryRequest, AssistantQueryResponse, RetrievalResponse
from app.services.analytics import AnalyticsService
from app.services.assistant_chat import AssistantChatService
from app.services.assistant_features import AssistantFeatureService
from app.services.chat_memory import ChatMemoryService
from app.services.rag_pipeline import RAGRetrievalService
from app.services.vector_store import get_vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _sanitized_document_ids(document_ids: list[str]) -> list[str]:
    return [item for item in document_ids if item]


def check_chat_rate_limit(user_id: str, limit: int = 20, window_seconds: int = 300) -> None:
    import time
    from collections import deque
    from fastapi import HTTPException
    
    key = f"chat-generation:{user_id}"
    now = time.time()
    cutoff = now - window_seconds

    with rate_limiter._lock:
        bucket = rate_limiter._buckets.setdefault(key, deque())
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = int(max(1.0, (bucket[0] + window_seconds) - now))
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down and try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)


async def _ensure_ollama_running() -> None:
    import httpx
    from app.core.config import settings
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(settings.OLLAMA_BASE_URL)
            res.raise_for_status()
    except Exception as exc:
        print(f"[CHAT ERROR] {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Ollama: {exc}"
        )


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    analytics = AnalyticsService(
        DocumentRepository(db),
        ConversationRepository(db),
        MessageRepository(db),
    ).build_overview(user=current_user)
    return DashboardSummary(
        title="AI Knowledge Assistant",
        description="Monitor private knowledge ingestion, local-only AI usage, and chat activity from one place.",
        stats=[{"label": metric.label, "value": metric.value} for metric in analytics.metrics],
    )


@router.get("/analytics", response_model=AnalyticsOverview)
async def get_analytics_overview(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsOverview:
    apply_rate_limit(request, scope="assistant-analytics", limit=40, user_id=str(current_user.id))
    return AnalyticsService(
        DocumentRepository(db),
        ConversationRepository(db),
        MessageRepository(db),
    ).build_overview(user=current_user)


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_context(
    payload: AssistantQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RetrievalResponse:
    apply_rate_limit(request, scope="assistant-retrieve", limit=30, user_id=str(current_user.id))
    payload.query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")
    # retrieve() is now async — await it
    return await RAGRetrievalService(db).retrieve(
        user=current_user,
        query=payload.query,
        top_k=payload.top_k,
        hybrid=payload.hybrid,
        document_ids=_sanitized_document_ids(payload.document_ids),
    )


@router.post("/query", response_model=AssistantQueryResponse)
async def query_assistant(
    payload: AssistantQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantQueryResponse:
    await _ensure_ollama_running()
    check_chat_rate_limit(str(current_user.id))
    payload.query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")
    memory = ChatMemoryService(db)
    conversation = memory.get_or_create_conversation(
        user=current_user,
        conversation_id=payload.conversation_id,
        initial_user_message=payload.query,
    )
    if payload.conversation_id is not None:
        memory.append_message(
            conversation=conversation,
            role="user",
            content=payload.query,
        )

    result = await AssistantChatService(get_vector_store_service()).answer(
        user=current_user,
        query=payload.query,
        model=payload.model or settings.OLLAMA_DEFAULT_MODEL,
        top_k=payload.top_k or 4,
        document_ids=_sanitized_document_ids(payload.document_ids),
    )
    updated_conversation = memory.sync_conversation_after_response(
        conversation=conversation,
        user_message=payload.query,
        assistant_message=result["answer"],
    )
    result["conversation_id"] = updated_conversation.id
    result["conversation_title"] = updated_conversation.title
    return AssistantQueryResponse(**result)


@router.post("/chat/stream")
async def stream_assistant_chat(
    payload: AssistantQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    await _ensure_ollama_running()
    check_chat_rate_limit(str(current_user.id))
    payload.query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")

    memory = ChatMemoryService(db)
    conversation = memory.get_or_create_conversation(
        user=current_user,
        conversation_id=payload.conversation_id,
        initial_user_message=payload.query,
    )
    if payload.conversation_id is not None:
        memory.append_message(
            conversation=conversation,
            role="user",
            content=payload.query,
        )

    # Snapshot IDs before entering the generator (avoid closed-session access)
    conversation_id = conversation.id
    conversation_title = conversation.title
    user_id = current_user.id

    async def event_stream():
        full_answer = ""
        try:
            assistant_stream = AssistantChatService(get_vector_store_service()).stream_answer(
                user_id=user_id,
                query=payload.query,
                model=payload.model or settings.OLLAMA_DEFAULT_MODEL,
                top_k=payload.top_k or 4,
                document_ids=_sanitized_document_ids(payload.document_ids),
            )

            async for chunk in assistant_stream:
                if not chunk.startswith("data: "):
                    yield chunk
                    continue

                payload_json = chunk[6:].strip()
                try:
                    data = json.loads(payload_json)
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed SSE chunk: %r", chunk)
                    continue

                if data.get("type") == "token":
                    full_answer += data.get("content", "")
                elif data.get("type") == "done":
                    # Persist the completed response in a fresh DB session
                    from app.db.session import db_manager
                    from app.models.conversation import Conversation

                    with db_manager.session_factory() as local_db:
                        local_memory = ChatMemoryService(local_db)
                        local_conversation = local_db.get(Conversation, conversation_id)
                        if local_conversation:
                            final_answer = full_answer.strip() or "I was unable to generate a response. Please try again."
                            
                            citations_list = data.get("citations", [])
                            citations_json = json.dumps(citations_list) if citations_list else None

                            updated = local_memory.sync_conversation_after_response(
                                conversation=local_conversation,
                                user_message=payload.query,
                                assistant_message=final_answer,
                                citations=citations_json,
                            )
                            data["conversation_id"] = str(updated.id)
                            data["conversation_title"] = updated.title
                        else:
                            data["conversation_id"] = str(conversation_id)
                            data["conversation_title"] = conversation_title
                elif data.get("type") == "context":
                    data["conversation_id"] = str(conversation_id)
                    data["conversation_title"] = conversation_title

                yield f"data: {json.dumps(data)}\n\n"

        except Exception as e:
            import traceback
            full_tb = traceback.format_exc()
            print(f"[STREAM CRASH]\n{full_tb}")
            error_payload = json.dumps({
                "type": "error",
                "message": str(e) or "Stream failed. Check backend logs."
            })
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/test-stream")
async def test_stream():
    import asyncio
    import json
    async def gen():
        for word in ["Hello", " from", " AI", " stream", " test!"]:
            yield f"data: {json.dumps({'type': 'token', 'content': word})}\n\n"
            await asyncio.sleep(0.1)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/summaries", response_model=AssistantSummaryResponse)
async def summarize_documents(
    payload: AssistantSummaryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantSummaryResponse:
    apply_rate_limit(request, scope="assistant-summaries", limit=20, user_id=str(current_user.id))
    payload.query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")
    result = await AssistantFeatureService(get_vector_store_service()).summarize_documents(
        user=current_user,
        query=payload.query,
        model=payload.model,
        document_ids=_sanitized_document_ids(payload.document_ids),
    )
    return AssistantSummaryResponse(**result)


@router.post("/quiz", response_model=AssistantQuizResponse)
async def generate_quiz(
    payload: AssistantSummaryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantQuizResponse:
    apply_rate_limit(request, scope="assistant-quiz", limit=20, user_id=str(current_user.id))
    payload.query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")
    result = await AssistantFeatureService(get_vector_store_service()).generate_quiz(
        user=current_user,
        query=payload.query,
        model=payload.model,
        document_ids=_sanitized_document_ids(payload.document_ids),
    )
    return AssistantQuizResponse(**result)


@router.post("/suggested-prompts", response_model=SuggestedPromptsResponse)
async def suggested_prompts(
    payload: AssistantSummaryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuggestedPromptsResponse:
    apply_rate_limit(request, scope="assistant-suggested-prompts", limit=60, user_id=str(current_user.id))
    payload.query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")
    result = await AssistantFeatureService(get_vector_store_service()).suggested_prompts(
        user=current_user,
        query=payload.query,
        model=payload.model,
        document_ids=_sanitized_document_ids(payload.document_ids),
    )
    return SuggestedPromptsResponse(**result)


@router.post("/document-search", response_model=SemanticDocumentSearchResponse)
async def semantic_document_search(
    payload: AssistantSummaryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SemanticDocumentSearchResponse:
    apply_rate_limit(request, scope="assistant-document-search", limit=30, user_id=str(current_user.id))
    safe_query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")

    vector_store = get_vector_store_service()
    search_results = await vector_store.similarity_search(
        user_id=current_user.id,
        query=safe_query,
        top_k=8,
    )

    seen: set[str] = set()
    results: list[SemanticDocumentSearchItem] = []
    repository = DocumentRepository(db)

    for result in search_results:
        document_id = result.metadata.get("document_id", "")
        if not document_id or document_id in seen:
            continue
        seen.add(document_id)

        try:
            doc_uuid = uuid.UUID(document_id)
            document = repository.get_by_user(doc_uuid, current_user.id)
            results.append(
                SemanticDocumentSearchItem(
                    document_id=document_id,
                    title=result.metadata.get("document_title", "Unknown"),
                    filename=result.metadata.get("filename", "unknown"),
                    excerpt=result.document[:220],
                    score=result.semantic_score,
                    tags=[
                        item.strip()
                        for item in (document.tags or "").split(",")
                        if item.strip()
                    ]
                    if document
                    else [],
                )
            )
        except (ValueError, TypeError):
            continue

    return SemanticDocumentSearchResponse(results=results)


@router.post("/notes", response_model=StudyNotesResponse)
async def generate_study_notes(
    payload: StudyNotesRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudyNotesResponse:
    apply_rate_limit(request, scope="assistant-study-notes", limit=20, user_id=str(current_user.id))
    payload.query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")
    result = await AssistantFeatureService(get_vector_store_service()).generate_study_notes(
        user=current_user,
        query=payload.query,
        model=payload.model,
        document_ids=_sanitized_document_ids(payload.document_ids),
    )
    return StudyNotesResponse(**result)

