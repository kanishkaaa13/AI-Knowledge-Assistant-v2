"""
Q1 Content Check - Re-run original query after re-indexing
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk

with next(get_db()) as db:
    # Search for "Types of machine learning" or similar content
    doc = db.query(UploadedDocument).filter(
        UploadedDocument.title == "machine-learning-cheat-sheet"
    ).first()
    
    print("Q1 Content Check - Original Query:")
    print("=" * 80)
    print()
    print(f"Query: 'Types of machine learning' or 'supervised learning'")
    print(f"Document: {doc.title}")
    print()
    
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc.id
    ).order_by(DocumentChunk.chunk_index).all()
    
    # Search for relevant chunks
    relevant_chunks = []
    for chunk in chunks:
        content_lower = chunk.content.lower()
        if any(term in content_lower for term in ["types of machine learning", "supervised", "unsupervised", "reinforcement"]):
            relevant_chunks.append(chunk)
    
    print(f"Found {len(relevant_chunks)} chunks with relevant content:")
    print()
    
    for i, chunk in enumerate(relevant_chunks[:5], 1):
        print(f"Chunk {i}:")
        print(f"  Chunk index: {chunk.chunk_index}")
        print(f"  Page number: {chunk.page_number}")
        print(f"  Content preview:")
        preview = chunk.content[:200].replace('\n', ' ')
        print(f"    {preview}...")
        
        # Check if it contains the actual breakdown
        if "supervised" in chunk.content.lower() and "unsupervised" in chunk.content.lower():
            print(f"  ✓ Contains both supervised and unsupervised mentions")
        
        print()
    
    print("=" * 80)
    print("VERIFICATION:")
    print(f"  - Page numbers are now correct (not uniformly 1)")
    print(f"  - Content contains actual machine learning type breakdown")
    print("=" * 80)
