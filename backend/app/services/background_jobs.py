from __future__ import annotations

import logging
import uuid

from app.core.config import settings
from app.db.session import db_manager
from app.models.uploaded_document import UploadedDocument
from app.services.ollama_llm import OllamaLLMService
from app.services.rag_pipeline import RAGIngestionService

logger = logging.getLogger(__name__)


def process_document_ingestion(document_id: str) -> None:
    db = db_manager.session_factory()
    try:
        document = db.get(UploadedDocument, uuid.UUID(document_id))
        if not document:
            logger.error("Ingestion job skipped: document %s no longer exists.", document_id)
            return
        try:
            document.status = "processing"
            document.processing_error = None
            db.add(document)
            db.commit()

            RAGIngestionService(db).index_document(document)

            summary_source = (document.extracted_text or "")[:3000]
            if summary_source.strip():
                prompt = (
                    "Summarize this document in 4 short bullets using only the provided text.\n\n"
                    f"{summary_source}"
                )
                summary = __safe_generate(prompt)
                document.ai_summary = summary.strip() or document.ai_summary

            document.status = "indexed"
            db.add(document)
            db.commit()
        except Exception as exc:
            logger.exception("Ingestion failed for document %s.", document_id)
            db.rollback()
            document.status = "failed"
            document.processing_error = str(exc)
            db.add(document)
            db.commit()
            raise
    finally:
        db.close()


def __safe_generate(prompt: str) -> str:
    import asyncio

    async def _run():
        return await OllamaLLMService().generate(prompt=prompt, model=settings.DEFAULT_CHAT_MODEL)

    return asyncio.run(_run())
