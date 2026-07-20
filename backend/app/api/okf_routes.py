import os
import uuid
import json
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import settings
from app.services.document_processor import DocumentProcessor
from app.services.okf_converter import OKFConverterService
from app.services.okf_retriever import OKFRetrieverService
from app.services.ollama_llm import OllamaLLMService

logger = logging.getLogger(__name__)

router = APIRouter()


class OKFChatRequest(BaseModel):
    bundle_id: str
    query: str


@router.post("/documents/upload-okf", status_code=status.HTTP_201_CREATED)
async def upload_document_okf(
    file: UploadFile = File(...),
) -> dict:
    """
    Experimental OKF Upload:
    Extracts text from the uploaded file, splits it into structured concepts,
    calls the default LLM to generate concept metadata, writes the OKF bundle to disk,
    and returns the bundle ID.
    """
    logger.info("OKF Upload received file: %s", file.filename)
    
    file_bytes = await file.read()
    file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ".txt"
    
    # Reuse existing text extraction pipeline
    processor = DocumentProcessor()
    try:
        text, _ = processor.extract_text(file_bytes, file_extension)
    except Exception as exc:
        logger.error("Failed text extraction in OKF upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse file: {exc}"
        )
        
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Extracted text from the uploaded file is empty."
        )
        
    bundle_id = str(uuid.uuid4())
    document_title = os.path.splitext(file.filename)[0].replace("-", " ").replace("_", " ").title() if file.filename else "Document"
    
    # Convert to OKF structured bundle
    converter = OKFConverterService()
    try:
        await converter.convert_to_okf_bundle(
            document_id=bundle_id,
            document_title=document_title,
            text=text
        )
    except Exception as exc:
        logger.error("Failed to generate OKF bundle: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OKF bundle: {exc}"
        )
        
    return {
        "bundle_id": bundle_id,
        "document_title": document_title,
        "message": "OKF bundle successfully generated."
    }


@router.post("/chat/okf-stream")
async def chat_okf_stream(
    payload: OKFChatRequest
) -> StreamingResponse:
    """
    Experimental OKF Retrieval & Generation Stream:
    Takes a bundle_id and user query, retrieves matching concepts,
    and streams back a contextual answer from the default LLM.
    """
    backend_dir = Path(__file__).resolve().parent.parent.parent
    bundle_dir = backend_dir / "okf_bundles" / payload.bundle_id
    
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        logger.warning("OKF bundle_id not found: %s", payload.bundle_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OKF bundle with ID '{payload.bundle_id}' was not found on this server."
        )
        
    # Retrieve relevant concept files and link-following connections
    retriever = OKFRetrieverService()
    try:
        concepts = await retriever.retrieve_concepts(str(bundle_dir), payload.query)
    except Exception as exc:
        logger.error("OKF concept retrieval failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve concept context: {exc}"
        )
        
    # Build prompt from retrieved concepts context
    context_str = ""
    for idx, c in enumerate(concepts, start=1):
        context_str += (
            f"Concept {idx}: {c['title']}\n"
            f"Description: {c['description']}\n"
            f"Tags: {', '.join([f'#{t}' for t in c['tags']])}\n"
            f"Content:\n{c['body']}\n"
            "--------------------------------------------------\n\n"
        )
        
    prompt = (
        "You are an expert AI knowledge assistant.\n"
        "Your task is to answer the user query based ONLY on the following OKF concepts retrieved from their workspace.\n"
        "If the answer cannot be found in the provided context, state that the context has insufficient information.\n\n"
        "OKF CONCEPTS CONTEXT:\n"
        f"{context_str}"
        f"USER QUERY: {payload.query}\n\n"
        "CONCISE DETAILED RESPONSE:"
    )
    
    async def event_generator():
        try:
            # 1. Yield retrieved context first so UI/tests can see which concept files were selected
            concept_metadata = [
                {
                    "filename": c["filename"],
                    "title": c["title"],
                    "description": c["description"],
                    "tags": c["tags"],
                    "retrieved_via": c["retrieved_via"]
                }
                for c in concepts
            ]
            yield f"data: {json.dumps({'type': 'context', 'concepts': concept_metadata})}\n\n"
            
            # 2. Stream answer tokens from the LLM
            llm = OllamaLLMService()
            async for token in llm.stream_generate(prompt=prompt):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
            # 3. Stream final completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as stream_exc:
            logger.exception("Error during OKF streaming generation")
            yield f"data: {json.dumps({'type': 'error', 'message': str(stream_exc)})}\n\n"
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
