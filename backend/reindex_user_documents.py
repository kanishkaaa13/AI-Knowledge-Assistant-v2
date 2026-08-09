"""
Re-run ingestion pipeline for a specific user's documents.
This rebuilds ChromaDB vectors from SQL document_chunks.
"""

import uuid
from app.db.session import get_db
from app.models.user import User
from app.models.uploaded_document import UploadedDocument
from app.services.rag_pipeline import RAGIngestionService

user_id_str = "12b2f540-96bf-4b44-92da-f263524a8662"
user_id = uuid.UUID(user_id_str)

# Skip delete_document_index since collections are already deleted
# We'll directly create new chunks without trying to delete old ones

print("=" * 80)
print(f"RE-INDEXING DOCUMENTS FOR USER: {user_id_str}")
print("=" * 80)
print()

with next(get_db()) as db:
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"User {user_id_str} not found")
        exit(1)
    
    print(f"User: {user.email}")
    print()
    
    # Get documents for this user
    documents = db.query(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    print(f"Found {len(documents)} documents")
    print()
    
    # Initialize ingestion service
    ingestion_service = RAGIngestionService(db)
    
    for idx, doc in enumerate(documents, 1):
        print(f"[{idx}/{len(documents)}] Re-indexing: {doc.title}")
        print(f"  Filename: {doc.file_name}")
        print(f"  Current status: {doc.status}")
        
        try:
            chunks = ingestion_service.index_document(doc)
            print(f"  ✓ Re-indexed successfully ({len(chunks)} chunks)")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()

print("=" * 80)
print("RE-INDEXING COMPLETE")
print("=" * 80)
