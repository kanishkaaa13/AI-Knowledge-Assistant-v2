from __future__ import annotations

import logging
import uuid

from langchain_core.tools import tool

from app.core.config import settings
from app.db.session import db_manager
from app.models.user import User
from app.services.assistant_features import AssistantFeatureService
from app.services.bm25_index import get_bm25_service
from app.services.chat_memory import ChatMemoryService
from app.services.flashcard_service import FlashcardService
from app.services.vector_store import get_vector_store_service

logger = logging.getLogger(__name__)


@tool
async def search_documents(query: str, top_k: int = 4, user_id: str | None = None) -> str:
    """Search documents using semantic similarity (vector embeddings). Best for conceptual queries, synonyms, and meaning-based retrieval.

    Use this when the user asks about concepts, ideas, or topics that may be expressed differently in the text.
    This uses ChromaDB vector embeddings to find semantically similar content even if exact words don't match.

    Args:
        query: The search query string (semantic/conceptual search).
        top_k: Number of relevant chunks to retrieve.
        user_id: User ID string (auto-injected from context, do not provide manually).
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
    query: str = "Summarize the document",
    model: str = settings.DEFAULT_CHAT_MODEL,
    user_id: str | None = None
) -> str:
    """Summarize a document given its document ID using the existing summary service.

    Args:
        doc_id: The UUID or string ID of the document to summarize.
        query: Focus query for summarization.
        model: LLM model name to use.
        user_id: User ID string (auto-injected from context, do not provide manually).
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


@tool
async def keyword_search(query: str, top_k: int = 4, user_id: str | None = None) -> str:
    """Search documents using BM25 keyword search for exact term matching. Best for finding specific words, phrases, or technical terms.

    Use this when the user is looking for exact words, specific terminology, names, or precise phrases.
    This uses BM25 keyword matching to find chunks containing the exact terms in the query.
    Unlike semantic search, this requires exact word matches and is better for precise term lookup.

    Args:
        query: The search query string (keyword/term-based search).
        top_k: Number of relevant chunks to retrieve.
        user_id: User ID string (auto-injected from context, do not provide manually).
    """
    try:
        uid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000000")
        bm25_service = get_bm25_service()
        results = bm25_service.search(user_id=uid, query=query, top_k=top_k)

        if not results:
            return "No relevant document chunks found via keyword search."

        formatted_chunks = []
        for idx, (chunk_id, score) in enumerate(results, 1):
            formatted_chunks.append(f"[{idx}] Chunk ID: {chunk_id}, BM25 Score: {score:.4f}")
        return "\n\n".join(formatted_chunks)
    except Exception as e:
        logger.exception("Error in keyword_search tool: %s", e)
        return f"Error executing keyword search: {e}"


@tool
async def flashcard_generator(
    document_ids: str,
    query: str | None = None,
    count: int = 5,
    model: str = settings.DEFAULT_CHAT_MODEL,
    user_id: str | None = None
) -> str:
    """Generate flashcards from selected documents using the existing flashcard service.

    Args:
        document_ids: Comma-separated list of document IDs (UUIDs) to generate flashcards from.
        query: Optional focus query for flashcard generation.
        count: Number of flashcards to generate.
        model: LLM model name to use.
        user_id: User ID string (auto-injected from context, do not provide manually).
    """
    try:
        uid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000000")
        
        # Parse and validate document_ids
        doc_ids_list = [doc_id.strip() for doc_id in document_ids.split(",") if doc_id.strip()]
        
        if not doc_ids_list:
            return "Error: No valid document IDs provided. Please provide comma-separated document IDs."
        
        # Validate each ID is a valid UUID
        valid_doc_ids = []
        for doc_id in doc_ids_list:
            try:
                uuid.UUID(doc_id)
                valid_doc_ids.append(doc_id)
            except ValueError:
                logger.warning(f"Invalid UUID in document_ids: {doc_id}")
        
        if not valid_doc_ids:
            return "Error: No valid UUIDs found in document_ids. Please provide valid document UUIDs."

        with db_manager.session_factory() as db:
            user = User()
            user.id = uid
            flashcard_service = FlashcardService(db)
            flashcards = await flashcard_service.generate_flashcards(
                user=user,
                document_ids=valid_doc_ids,
                query=query,
                count=count,
                model=model
            )

        if not flashcards:
            return "Unable to generate flashcards from the specified documents."

        formatted_cards = []
        for idx, card in enumerate(flashcards, 1):
            formatted_cards.append(f"[{idx}] Q: {card.question}\n    A: {card.answer}")
        return "\n\n".join(formatted_cards)
    except Exception as e:
        logger.exception("Error in flashcard_generator tool: %s", e)
        return f"Error generating flashcards: {e}"


@tool
async def quiz_generator(
    document_ids: str,
    query: str = "Generate a quiz",
    count: int = 5,
    model: str = settings.DEFAULT_CHAT_MODEL,
    user_id: str | None = None
) -> str:
    """Generate a quiz from selected documents using the existing quiz generation service.

    Args:
        document_ids: Comma-separated list of document IDs (UUIDs) to generate quiz from.
        query: Quiz topic or focus query.
        count: Number of quiz questions to generate.
        model: LLM model name to use.
        user_id: User ID string (auto-injected from context, do not provide manually).
    """
    try:
        uid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000000")
        
        # Parse and validate document_ids
        doc_ids_list = [doc_id.strip() for doc_id in document_ids.split(",") if doc_id.strip()]
        
        if not doc_ids_list:
            return "Error: No valid document IDs provided. Please provide comma-separated document IDs."
        
        # Validate each ID is a valid UUID
        valid_doc_ids = []
        for doc_id in doc_ids_list:
            try:
                uuid.UUID(doc_id)
                valid_doc_ids.append(doc_id)
            except ValueError:
                logger.warning(f"Invalid UUID in document_ids: {doc_id}")
        
        if not valid_doc_ids:
            return "Error: No valid UUIDs found in document_ids. Please provide valid document UUIDs."

        vector_store = get_vector_store_service()
        feature_service = AssistantFeatureService(vector_store)

        user = User()
        user.id = uid

        res = await feature_service.generate_quiz(
            user=user,
            query=query,
            document_ids=valid_doc_ids,
            count=count,
            model=model
        )

        if not res or "quiz" not in res:
            return "Unable to generate quiz from the specified documents."

        quiz_data = res["quiz"]
        formatted_quiz = []
        for idx, question in enumerate(quiz_data, 1):
            formatted_quiz.append(f"[{idx}] Q: {question.get('question', 'N/A')}\n    A: {question.get('answer', 'N/A')}")
        return "\n\n".join(formatted_quiz)
    except Exception as e:
        logger.exception("Error in quiz_generator tool: %s", e)
        return f"Error generating quiz: {e}"


@tool
def export_notes(conversation_id: str, user_id: str | None = None) -> str:
    """Export conversation notes as formatted text using the existing export service.

    Args:
        conversation_id: The UUID of the conversation to export.
        user_id: User ID string (auto-injected from context, do not provide manually).
    """
    try:
        uid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000000")
        conv_id = uuid.UUID(conversation_id)

        with db_manager.session_factory() as db:
            user = User()
            user.id = uid
            chat_memory = ChatMemoryService(db)
            exported = chat_memory.export_conversation(user=user, conversation_id=conv_id)

        return exported
    except Exception as e:
        logger.exception("Error in export_notes tool: %s", e)
        return f"Error exporting conversation notes: {e}"
