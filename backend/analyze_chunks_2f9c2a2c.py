"""
Analyze chunks for user 2f9c2a2c to understand boilerplate patterns.
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

print("=" * 80)
print("CHUNK ANALYSIS FOR USER 2f9c2a2c")
print("=" * 80)
print()

with next(get_db()) as db:
    documents = db.query(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    
    for doc in documents:
        print(f"Document: {doc.title}")
        print(f"  Filename: {doc.file_name}")
        print(f"  Total chunks: {len(doc.chunks)}")
        print()
        
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index).all()
        
        # Show first 10 chunks to identify boilerplate patterns
        print(f"  First 10 chunks:")
        for i, chunk in enumerate(chunks[:10], 1):
            content_preview = chunk.content[:200].replace('\n', ' ')
            print(f"    [{i}] Page {chunk.page_number}, Chunk {chunk.chunk_index}")
            print(f"        Content: {content_preview}...")
            print()
        
        # Show last 5 chunks
        print(f"  Last 5 chunks:")
        for i, chunk in enumerate(chunks[-5:], len(chunks)-4):
            content_preview = chunk.content[:200].replace('\n', ' ')
            print(f"    [{i}] Page {chunk.page_number}, Chunk {chunk.chunk_index}")
            print(f"        Content: {content_preview}...")
            print()
        
        print("-" * 80)
        print()
