from __future__ import annotations

import logging
import uuid

from langchain_core.tools import tool

from app.models.user import User
from app.services.assistant_features import AssistantFeatureService
from app.services.vector_store import get_vector_store_service

logger = logging.getLogger(__name__)


@tool
async def search_documents(query: str, user_id: str | None = None, top_k: int = 4) -> str:
    """Search ChromaDB vector store for relevant document chunks matching the query.

    Args:
        query: The search query string.
        user_id: Optional user ID string to scope vector search.
        top_k: Number of relevant chunks to retrieve.
    """
    try:
        vector_store = get_vector_store_service()
        uid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000000")
        results = await vector_store.similarity_search(user_id=uid, query=query, top_k=top_k)

        if not results:
            return "No relevant document chunks found."

        formatted_chunks = []
        for idx, res in enumerate(results, 1):
            formatted_chunks.append(f"[{idx}] (ID: {res.id})\n{res.document}")
        return "\n\n".join(formatted_chunks)
    except Exception as e:
        logger.exception("Error in search_documents tool: %s", e)
        return f"Error executing document search: {e}"


@tool
async def summarize_document(
    doc_id: str,
    user_id: str | None = None,
    query: str = "Summarize the document",
    model: str = "llama3.2",
) -> str:
    """Summarize a document given its document ID using the existing summary service.

    Args:
        doc_id: The UUID or string ID of the document to summarize.
        user_id: Optional user ID string.
        query: Focus query for summarization.
        model: LLM model name to use.
    """
    try:
        vector_store = get_vector_store_service()
        feature_service = AssistantFeatureService(vector_store)

        user = User()
        user.id = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000000")

        res = await feature_service.summarize_documents(
            user=user,
            query=query,
            model=model,
            document_ids=[doc_id],
        )
        return res.get("summary", "Unable to generate summary for the specified document.")
    except Exception as e:
        logger.exception("Error in summarize_document tool: %s", e)
        return f"Error executing document summarization: {e}"


@tool
def answer_general_knowledge(query: str) -> str:
    """Pass-through tool for general knowledge queries where document context is not required.

    Args:
        query: General knowledge query.
    """
    return query
