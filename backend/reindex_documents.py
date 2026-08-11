"""
Re-index all PDF documents to fix page numbers
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.services.rag_pipeline import RAGIngestionService

with next(get_db()) as db:
    # Get all PDF documents
    documents = db.query(UploadedDocument).filter(
        UploadedDocument.file_extension == ".pdf"
    ).all()
    
    print("Re-indexing PDF documents:")
    print("=" * 80)
    print()
    
    ingestion_service = RAGIngestionService(db)
    
    for doc in documents:
        print(f"Document: {doc.title}")
        print(f"  File: {doc.file_name}")
        print(f"  Current chunks: {len(doc.chunks) if hasattr(doc, 'chunks') else 'N/A'}")
        
        try:
            chunks = ingestion_service.index_document(doc)
            print(f"  ✓ Re-indexed successfully")
            print(f"  New chunk count: {len(chunks)}")
        except Exception as e:
            print(f"  ✗ Re-index failed: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 80)
    print("Re-indexing complete")
