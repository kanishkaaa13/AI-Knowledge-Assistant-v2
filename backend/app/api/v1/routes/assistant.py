import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import apply_rate_limit
from app.core.sanitize import ensure_present, sanitize_text
from app.db.session import db_manager, get_db
from app.models.conversation import Conversation
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


async def check_chat_rate_limit(
    request: Request,
    user_id: str,
    limit: int = 20,
    window_seconds: int = 300,
) -> None:
    await apply_rate_limit(
        request,
        scope="chat-generation",
        limit=limit,
        user_id=user_id,
        window_seconds=window_seconds,
    )


def _prepare_chat_turn(
    payload: AssistantQueryRequest,
    current_user: User,
    db: Session,
) -> tuple[ChatMemoryService, Conversation]:
    """Sanitize the incoming query and attach it to a (new or existing) conversation."""
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
    return memory, conversation


def _assistant_stream_response(
    payload: AssistantQueryRequest,
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    conversation_title: str,
) -> StreamingResponse:
    """Stream assistant tokens as SSE, persisting the final answer once complete.

    Conversation identifiers are snapshotted by the caller so the generator never
    touches the request-scoped (already closed) DB session.
    """

    async def event_stream():
        full_answer = ""
        try:
            assistant_stream = AssistantChatService(get_vector_store_service()).stream_answer(
                user_id=user_id,
                query=payload.query,
                model=payload.model or settings.DEFAULT_CHAT_MODEL,
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
                    with db_manager.session_factory() as local_db:
                        local_memory = ChatMemoryService(local_db)
                        local_conversation = local_db.get(Conversation, conversation_id)
                        if local_conversation:
                            final_answer = (
                                full_answer.strip()
                                or "I was unable to generate a response. Please try again."
                            )
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

        except Exception as exc:
            logger.exception("Assistant stream crashed.")
            error_payload = json.dumps(
                {
                    "type": "error",
                    "message": str(exc) or "Stream failed. Check backend logs.",
                }
            )
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
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
    await apply_rate_limit(request, scope="assistant-analytics", limit=40, user_id=str(current_user.id))
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
    await apply_rate_limit(request, scope="assistant-retrieve", limit=30, user_id=str(current_user.id))
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
    await check_chat_rate_limit(request, str(current_user.id))
    memory, conversation = _prepare_chat_turn(payload, current_user, db)

    result = await AssistantChatService(get_vector_store_service()).answer(
        user=current_user,
        query=payload.query,
        model=payload.model or settings.DEFAULT_CHAT_MODEL,
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


@router.post("/query/stream")
async def stream_query_assistant(
    payload: AssistantQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    await check_chat_rate_limit(request, str(current_user.id))
    _, conversation = _prepare_chat_turn(payload, current_user, db)

    return _assistant_stream_response(
        payload,
        user_id=current_user.id,
        conversation_id=conversation.id,
        conversation_title=conversation.title,
    )


@router.post("/chat/stream")
async def stream_assistant_chat(
    payload: AssistantQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    await check_chat_rate_limit(request, str(current_user.id))
    _, conversation = _prepare_chat_turn(payload, current_user, db)

    return _assistant_stream_response(
        payload,
        user_id=current_user.id,
        conversation_id=conversation.id,
        conversation_title=conversation.title,
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
    await apply_rate_limit(request, scope="assistant-summaries", limit=20, user_id=str(current_user.id))
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
    await apply_rate_limit(request, scope="assistant-quiz", limit=20, user_id=str(current_user.id))
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
    await apply_rate_limit(request, scope="assistant-suggested-prompts", limit=60, user_id=str(current_user.id))
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
    await apply_rate_limit(request, scope="assistant-document-search", limit=30, user_id=str(current_user.id))
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
    await apply_rate_limit(request, scope="assistant-study-notes", limit=20, user_id=str(current_user.id))
    payload.query = ensure_present(sanitize_text(payload.query, max_length=4000), field_name="query")
    result = await AssistantFeatureService(get_vector_store_service()).generate_study_notes(
        user=current_user,
        query=payload.query,
        model=payload.model,
        document_ids=_sanitized_document_ids(payload.document_ids),
    )
    return StudyNotesResponse(**result)

