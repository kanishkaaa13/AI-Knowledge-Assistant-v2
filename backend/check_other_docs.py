"""
Check if other documents for this user have the same page assignment issue
"""

import uuid
from app.db.session import get_db
from app.models.document_chunk import DocumentChunk
from app.models.uploaded_document import UploadedDocument

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

with next(get_db()) as db:
    documents = db.query(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    
    print(f"User has {len(documents)} documents:")
    print()
    
    for doc in documents:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"  DB page_count: {doc.page_count}")
        
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
        
        if chunks:
            page_counts = {}
            for chunk in chunks:
                page = chunk.page_number
                page_counts[page] = page_counts.get(page, 0) + 1
            
            unique_pages = len(page_counts)
            print(f"  Chunks: {len(chunks)}")
            print(f"  Unique page numbers in chunks: {unique_pages}")
            
            if unique_pages == 1:
                print(f"  ⚠ ALL chunks on page {list(page_counts.keys())[0]}")
            else:
                print(f"  Page distribution: {dict(sorted(page_counts.items())[:5])}...")
        else:
            print(f"  No chunks")
        print()
