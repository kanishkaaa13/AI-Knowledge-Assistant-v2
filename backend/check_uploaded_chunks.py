"""
Check chunks for the newly uploaded document
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk

with next(get_db()) as db:
    # Find the most recently uploaded document
    doc = db.query(UploadedDocument).filter(
        UploadedDocument.title == "API Test Document"
    ).order_by(UploadedDocument.created_at.desc()).first()
    
    print("Checking Chunks for Uploaded Document:")
    print("=" * 80)
    print()
    
    if doc:
        print(f"Document: {doc.title}")
        print(f"  ID: {doc.id}")
        print(f"  Page count: {doc.page_count}")
        print()
        
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).order_by(DocumentChunk.chunk_index).all()
        
        print(f"Total chunks: {len(chunks)}")
        
        if chunks:
            page_numbers = [chunk.page_number for chunk in chunks]
            unique_pages = sorted(set(page_numbers))
            
            print(f"Unique page numbers: {unique_pages}")
            print(f"Page range: {min(unique_pages)} - {max(unique_pages)}")
            print()
            
            if all(p == 1 for p in page_numbers):
                print(f"✗ FAIL: All chunks assigned to page 1")
            else:
                print(f"✓ PASS: Chunks distributed across multiple pages")
            
            print()
            print("Sample chunks:")
            for chunk in chunks[:5]:
                preview = chunk.content[:50].replace('\n', ' ')
                print(f"  Chunk {chunk.chunk_index}: Page {chunk.page_number} - '{preview}...'")
        else:
            print("No chunks found (document may still be processing)")
    else:
        print("Document not found")
    
    print()
    print("=" * 80)
