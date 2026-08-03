"""
Test for circular import errors between vector_store.py and reranker.py
"""
import sys
sys.path.append(".")

print("Testing imports for circular dependency...")

try:
    from app.services.vector_store import VectorSearchResult
    print("✓ Successfully imported VectorSearchResult from vector_store")
except ImportError as e:
    print(f"✗ Failed to import VectorSearchResult: {e}")
    sys.exit(1)

try:
    from app.services.reranker import get_reranker_service
    print("✓ Successfully imported get_reranker_service from reranker")
except ImportError as e:
    print(f"✗ Failed to import get_reranker_service: {e}")
    sys.exit(1)

try:
    from app.services.rag_pipeline import RAGIngestionService
    print("✓ Successfully imported RAGIngestionService from rag_pipeline")
except ImportError as e:
    print(f"✗ Failed to import RAGIngestionService: {e}")
    sys.exit(1)

try:
    from app.services.assistant_chat import AssistantChatService
    print("✓ Successfully imported AssistantChatService from assistant_chat")
except ImportError as e:
    print(f"✗ Failed to import AssistantChatService: {e}")
    sys.exit(1)

print("\n✓ All imports successful - no circular import errors detected")
