"""
Re-run ingestion pipeline for a specific user's documents.
This rebuilds ChromaDB vectors from SQL document_chunks.
Bypasses delete_document_index since collections are already deleted.
"""

import uuid
from app.db.session import get_db
from app.models.user import User
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk
from app.repositories.chunk import DocumentChunkRepository
from app.services.vector_store import VectorStoreService, VectorRecord

user_id_str = "2f9c2a2c-2dac-4596-b117-6b2cffe01425"
user_id = uuid.UUID(user_id_str)

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
    
    # Initialize services
    chunk_repository = DocumentChunkRepository(db)
    vector_store = VectorStoreService()
    
    for idx, doc in enumerate(documents, 1):
        print(f"[{idx}/{len(documents)}] Re-indexing: {doc.title}")
        print(f"  Filename: {doc.file_name}")
        print(f"  Current status: {doc.status}")
        
        try:
            # Get existing chunks from SQL
            chunks = chunk_repository.list_by_document(doc.id)
            print(f"  Found {len(chunks)} SQL chunks")
            
            # Create vector records from SQL chunks
            vector_records = []
            for chunk in chunks:
                metadata = {
                    "document_id": str(doc.id),
                    "document_title": doc.title,
                    "user_id": str(user_id),
                    "filename": doc.file_name,
                    "upload_timestamp": doc.created_at.isoformat(),
                    "tags": doc.tags or "",
                    "chunk_index": chunk.chunk_index,
                    "chunk_id": chunk.vector_id,
                    "page": str(chunk.page_number),
                    "paragraph_index": str(chunk.paragraph_index),
                }
                
                vector_records.append(
                    VectorRecord(
                        id=chunk.vector_id,
                        document=chunk.content,
                        metadata=metadata,
                    )
                )
            
            # Upsert vectors to ChromaDB
            print(f"  Upserting {len(vector_records)} vectors to ChromaDB...")
            vector_store.upsert_vectors(user_id=user_id, records=vector_records)
            
            # Update document status
            doc.status = "indexed"
            doc.processing_error = None
            db.add(doc)
            db.commit()
            
            print(f"  ✓ Re-indexed successfully ({len(vector_records)} vectors)")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()

print("=" * 80)
print("RE-INDEXING COMPLETE")
print("=" * 80)
