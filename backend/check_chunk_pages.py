"""
Check page numbers assigned to chunks for machine-learning-cheat-sheet.pdf
"""

import uuid
from app.db.session import get_db
from app.models.document_chunk import DocumentChunk
from app.models.uploaded_document import UploadedDocument

document_id = uuid.UUID("7488d639-ab79-4eb3-b809-06ab42e157b8")

with next(get_db()) as db:
    # Get document info
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if doc:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"Page count: {doc.page_count}")
        print()
    
    # Get chunks with their page numbers
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
    
    print(f"Total chunks: {len(chunks)}")
    print()
    
    # Show page distribution
    page_counts = {}
    for chunk in chunks:
        page = chunk.page_number
        page_counts[page] = page_counts.get(page, 0) + 1
    
    print("Page distribution:")
    for page in sorted(page_counts.keys()):
        print(f"  Page {page}: {page_counts[page]} chunks")
    print()
    
    # Show first 10 chunks with page numbers and content preview
    print("First 10 chunks:")
    for i, chunk in enumerate(chunks[:10]):
        preview = chunk.content[:100].replace('\n', ' ')
        print(f"  Chunk {chunk.chunk_index}: Page {chunk.page_number}, Para {chunk.paragraph_index}")
        print(f"    Content: {preview}...")
        print()
    
    # Search for chunks containing "Types of machine learning"
    print("Chunks containing 'Types of machine learning':")
    for chunk in chunks:
        if "Types of machine learning" in chunk.content or "types of machine learning" in chunk.content.lower():
            preview = chunk.content[:150].replace('\n', ' ')
            print(f"  Chunk {chunk.chunk_index}: Page {chunk.page_number}, Para {chunk.paragraph_index}")
            print(f"    Content: {preview}...")
            print()
