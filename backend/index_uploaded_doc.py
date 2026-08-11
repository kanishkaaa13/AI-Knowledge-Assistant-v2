"""
Manually index the uploaded document to complete the test
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.services.rag_pipeline import RAGIngestionService

with next(get_db()) as db:
    # Find the most recently uploaded document
    doc = db.query(UploadedDocument).filter(
        UploadedDocument.title == "API Test Document"
    ).order_by(UploadedDocument.created_at.desc()).first()
    
    print("Manually Indexing Uploaded Document:")
    print("=" * 80)
    print()
    
    if doc:
        print(f"Document: {doc.title}")
        print(f"  ID: {doc.id}")
        print(f"  Page count: {doc.page_count}")
        print()
        
        try:
            ingestion_service = RAGIngestionService(db)
            chunks = ingestion_service.index_document(doc)
            print(f"✓ Indexing successful")
            print(f"  Chunks created: {len(chunks)}")
        except Exception as e:
            print(f"✗ Indexing failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Document not found")
    
    print()
    print("=" * 80)
