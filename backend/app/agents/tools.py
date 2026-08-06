from __future__ import annotations

import logging
import uuid

from langchain_core.runnables import RunnableConfig
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
async def search_documents(query: str, top_k: int = 4, config: RunnableConfig | None = None) -> str:
    """Search documents using semantic similarity (vector embeddings). Best for conceptual queries, synonyms, and meaning-based retrieval.

    Use this when the user asks about concepts, ideas, or topics that may be expressed differently in the text.
    This uses ChromaDB vector embeddings to find semantically similar content even if exact words don't match.

    Args:
        query: The search query string (semantic/conceptual search). This must be a non-empty string containing the actual search terms from the user's request. Do not pass empty strings or placeholder text.
        top_k: Number of relevant chunks to retrieve. A value between 1 and 10 is recommended.
    """
    import time
    timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
    print(f"[search_documents] {timestamp} FUNCTION CALLED with query={query}, top_k={top_k}")
    logger.info(f"[search_documents] {timestamp} FUNCTION CALLED with query={query}, top_k={top_k}")
    
    # Validate query is not empty
    if not query or not query.strip():
        return "Error: Search query cannot be empty. Please provide a meaningful search term."
    
    try:
        # Get user_id from ContextVar (async-safe, isolated per request/task)
        import contextvars
        from app.agents.router_agent import _current_user_id
        
        user_id = _current_user_id.get()
        print(f"[search_documents] {timestamp} Extracted user_id from ContextVar: {user_id}")
        logger.info(f"[search_documents] {timestamp} Extracted user_id from ContextVar: {user_id}")
        
        if not user_id:
            raise ValueError("user_id missing from ContextVar - agent not properly configured")
        
        uid = uuid.UUID(user_id)
        print(f"[search_documents] UUID parsed: {uid}")
        logger.info(f"[search_documents] UUID parsed: {uid}")
        
        vector_store = get_vector_store_service()
        results = await vector_store.similarity_search(user_id=uid, query=query, top_k=top_k)

        if not results:
            print(f"[search_documents] {timestamp} FUNCTION EXIT - no results")
            return "No documents found matching the search query. No valid document ID is available. Do not attempt to call summarize_document without a valid doc_id from a successful search."

        formatted_chunks = []
        for idx, res in enumerate(results, 1):
            formatted_chunks.append(f"[{idx}] Document ID: {res.id}\n{res.document}")
        result = "\n\n".join(formatted_chunks)
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[search_documents] {timestamp} FUNCTION EXIT returning {len(results)} results")
        logger.info(f"[search_documents] {timestamp} FUNCTION EXIT returning {len(results)} results")
        return result
    except Exception as e:
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[search_documents] {timestamp} ERROR: {e}")
        logger.exception("Error in search_documents tool: %s", e)
        return f"Error executing document search: {e}"


@tool
async def summarize_document(
    doc_id: str,
    query: str = "Summarize the document",
    model: str = settings.DEFAULT_CHAT_MODEL,
    config: RunnableConfig | None = None
) -> str:
    """Summarize a document given its document ID using the existing summary service.

    Args:
        doc_id: The UUID string of the document to summarize. This must be a valid UUID like '550e8400-e29b-41d4-a716-446655440000'. You must extract this from the actual search results - do not use placeholder text or descriptions. If the search results show chunk IDs but not document IDs, ask the user to provide the specific document UUID they want summarized.
        query: A specific focus question or topic to guide the summarization. For example: 'What are the key findings about machine learning?' or 'Summarize the methodology section.'
        model: The specific LLM model to use for summarization. Use the exact model name string like 'llama3.1', 'mistral', or 'gpt-4'. Do not use placeholder text.
    """
    import time
    timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
    print(f"[summarize_document] {timestamp} FUNCTION CALLED with doc_id={doc_id}, query={query}")
    logger.info(f"[summarize_document] {timestamp} FUNCTION CALLED with doc_id={doc_id}, query={query}")
    try:
        # Get user_id from ContextVar (async-safe, isolated per request/task)
        import contextvars
        from app.agents.router_agent import _current_user_id
        
        user_id = _current_user_id.get()
        print(f"[summarize_document] {timestamp} Extracted user_id from ContextVar: {user_id}")
        logger.info(f"[summarize_document] {timestamp} Extracted user_id from ContextVar: {user_id}")
        
        if not user_id:
            raise ValueError("user_id missing from ContextVar - agent not properly configured")
        
        uid = uuid.UUID(user_id)
        print(f"[summarize_document] UUID parsed: {uid}")
        logger.info(f"[summarize_document] UUID parsed: {uid}")
        
        vector_store = get_vector_store_service()
        feature_service = AssistantFeatureService(vector_store)

        user = User()
        user.id = uid

        res = await feature_service.summarize_documents(
            user=user,
            query=query,
            model=model,
            document_ids=[doc_id],
        )
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[summarize_document] {timestamp} FUNCTION EXIT returning summary")
        logger.info(f"[summarize_document] {timestamp} FUNCTION EXIT returning summary")
        return res.get("summary", "Unable to generate summary for the specified document.")
    except Exception as e:
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[summarize_document] {timestamp} ERROR: {e}")
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
async def keyword_search(query: str, top_k: int = 4) -> str:
    """Search documents using BM25 keyword search for exact term matching. Best for finding specific words, phrases, or technical terms.

    Use this when the user is looking for exact words, specific terminology, names, or precise phrases.
    This uses BM25 keyword matching to find chunks containing the exact terms in the query.
    Unlike semantic search, this requires exact word matches and is better for precise term lookup.

    Args:
        query: The search query string (keyword/term-based search). Use exact words or phrases you want to find in the documents.
        top_k: Number of relevant chunks to retrieve. A value between 1 and 10 is recommended.
    """
    import time
    timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
    print(f"[keyword_search] {timestamp} FUNCTION CALLED with query={query}, top_k={top_k}")
    logger.info(f"[keyword_search] {timestamp} FUNCTION CALLED with query={query}, top_k={top_k}")
    try:
        # Get user_id from ContextVar (async-safe, isolated per request/task)
        import contextvars
        from app.agents.router_agent import _current_user_id
        
        user_id = _current_user_id.get()
        print(f"[keyword_search] {timestamp} Extracted user_id from ContextVar: {user_id}")
        logger.info(f"[keyword_search] {timestamp} Extracted user_id from ContextVar: {user_id}")
        
        if not user_id:
            raise ValueError("user_id missing from ContextVar - agent not properly configured")
        
        uid = uuid.UUID(user_id)
        print(f"[keyword_search] UUID parsed: {uid}")
        logger.info(f"[keyword_search] UUID parsed: {uid}")
        bm25_service = get_bm25_service()
        results = bm25_service.search(user_id=uid, query=query, top_k=top_k)
        print(f"[keyword_search] BM25 search returned {len(results) if results else 0} results for user {uid}")
        logger.info(f"[keyword_search] BM25 search returned {len(results) if results else 0} results for user {uid}")

        if not results:
            return "No relevant document chunks found via keyword search."

        formatted_chunks = []
        for idx, (chunk_id, score) in enumerate(results, 1):
            # Extract document_id from chunk_id (format: "document_id:chunk_index")
            doc_id = chunk_id.split(":")[0] if ":" in chunk_id else chunk_id
            formatted_chunks.append(f"[{idx}] Document ID: {doc_id}, Chunk ID: {chunk_id}, BM25 Score: {score:.4f}")
        result = "\n\n".join(formatted_chunks)
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[keyword_search] {timestamp} FUNCTION EXIT returning {len(results)} results")
        logger.info(f"[keyword_search] {timestamp} FUNCTION EXIT returning {len(results)} results")
        return result
    except Exception as e:
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[keyword_search] {timestamp} ERROR: {e}")
        logger.exception("Error in keyword_search tool: %s", e)
        return f"Error in keyword_search: {str(e)}"


@tool
async def flashcard_generator(
    document_ids: str,
    query: str | None = None,
    count: int = 5,
    model: str = settings.DEFAULT_CHAT_MODEL,
    config: RunnableConfig | None = None
) -> str:
    """Generate flashcards from selected documents using the existing flashcard service.

    Args:
        document_ids: Comma-separated list of document IDs (UUIDs) to generate flashcards from.
        query: Optional focus query for flashcard generation.
        count: Number of flashcards to generate.
        model: LLM model name to use.
    """
    try:
        # Get user_id from ContextVar (async-safe, isolated per request/task)
        import contextvars
        from app.agents.router_agent import _current_user_id
        
        user_id = _current_user_id.get()
        if not user_id:
            raise ValueError("user_id missing from ContextVar - agent not properly configured")
        uid = uuid.UUID(user_id)
        
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
    config: RunnableConfig | None = None
) -> str:
    """Generate a quiz from selected documents using the existing quiz generation service.

    Args:
        document_ids: Comma-separated list of document IDs (UUIDs) to generate quiz from.
        query: Quiz topic or focus query.
        count: Number of quiz questions to generate.
        model: LLM model name to use.
    """
    try:
        # Get user_id from ContextVar (async-safe, isolated per request/task)
        import contextvars
        from app.agents.router_agent import _current_user_id
        
        user_id = _current_user_id.get()
        if not user_id:
            raise ValueError("user_id missing from ContextVar - agent not properly configured")
        uid = uuid.UUID(user_id)
        
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
def export_notes(conversation_id: str, config: RunnableConfig | None = None) -> str:
    """Export conversation notes as formatted text using the existing export service.

    Args:
        conversation_id: The UUID of the conversation to export.
    """
    try:
        # Extract user_id from config (injected by agent framework)
        if not config or "configurable" not in config:
            raise ValueError("user_id missing from agent config - config not properly passed")
        user_id = config["configurable"].get("user_id")
        if not user_id:
            raise ValueError("user_id missing from agent config - user_id not set in configurable")
        uid = uuid.UUID(user_id)
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
