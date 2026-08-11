"""
Verify page attribution for migrated documents
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk

with next(get_db()) as db:
    # Check page number distribution for migrated documents
    documents = db.query(UploadedDocument).filter(
        UploadedDocument.file_extension == ".pdf"
    ).all()
    
    print("Page Attribution Verification:")
    print("=" * 80)
    print()
    
    for doc in documents:
        print(f"Document: {doc.title}")
        print(f"  File: {doc.file_name}")
        print(f"  DB page_count: {doc.page_count}")
        
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).order_by(DocumentChunk.chunk_index).all()
        
        if not chunks:
            print(f"  ⚠ No chunks found")
            continue
        
        # Get unique page numbers
        page_numbers = [chunk.page_number for chunk in chunks]
        unique_pages = sorted(set(page_numbers))
        
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Unique page numbers: {unique_pages}")
        print(f"  Page range: {min(unique_pages)} - {max(unique_pages)}")
        
        # Check if all are page 1 (the bug)
        if all(p == 1 for p in page_numbers):
            print(f"  ✗ FAIL: All chunks assigned to page 1")
        else:
            print(f"  ✓ PASS: Chunks distributed across multiple pages")
        
        # Show sample chunks with page numbers
        print(f"  Sample chunks:")
        for chunk in chunks[:5]:
            preview = chunk.content[:50].replace('\n', ' ')
            print(f"    Chunk {chunk.chunk_index}: Page {chunk.page_number} - '{preview}...'")
        
        print()
