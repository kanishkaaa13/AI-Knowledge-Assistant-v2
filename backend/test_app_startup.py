"""
Test that the app starts cleanly after config change.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("APP STARTUP TEST")
print("=" * 80)
print()

try:
    from app.core.config import settings
    print("✓ Config loaded")
    
    from app.db.session import db_manager
    print("✓ Database session manager initialized")
    
    from app.services.vector_store import get_vector_store_service
    vector_store = get_vector_store_service()
    print("✓ Vector store service initialized")
    
    from app.services.rag_pipeline import RAGIngestionService, RAGRetrievalService
    print("✓ RAG pipeline services initialized")
    
    print()
    print("✓ All core services start cleanly after config change")
    
except Exception as e:
    print(f"✗ Error during startup: {e}")
    import traceback
    traceback.print_exc()
