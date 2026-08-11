"""
Spot-check boilerplate chunks in 2 re-indexed docs (copyright/TOC exclusion)
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk

with next(get_db()) as db:
    # Check 2 specific documents for boilerplate exclusion
    test_docs = [
        "machine-learning-cheat-sheet",
        "Unit 3"
    ]
    
    print("Spot-Checking Boilerplate Chunks:")
    print("=" * 80)
    print()
    
    for doc_name in test_docs:
        doc = db.query(UploadedDocument).filter(
            UploadedDocument.title.ilike(f"%{doc_name}%")
        ).first()
        
        if not doc:
            print(f"✗ Document '{doc_name}' not found")
            continue
        
        print(f"Document: {doc.title}")
        print(f"  File: {doc.file_name}")
        print(f"  DB page_count: {doc.page_count}")
        print()
        
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).order_by(DocumentChunk.chunk_index).all()
        
        # Check for copyright/TOC indicators in early chunks
        early_chunks = chunks[:10] if len(chunks) >= 10 else chunks
        
        print(f"  Early chunks (first {len(early_chunks)}):")
        copyright_found = False
        toc_found = False
        
        for chunk in early_chunks:
            content_lower = chunk.content.lower()
            has_copyright = any(term in content_lower for term in ["copyright", "©", "all rights reserved"])
            has_toc = any(term in content_lower for term in ["table of contents", "contents", "chapter"])
            
            if has_copyright:
                copyright_found = True
                print(f"    Chunk {chunk.chunk_index} (Page {chunk.page_number}): Contains copyright")
                print(f"      Preview: {chunk.content[:100]}...")
            
            if has_toc:
                toc_found = True
                print(f"    Chunk {chunk.chunk_index} (Page {chunk.page_number}): Contains TOC")
                print(f"      Preview: {chunk.content[:100]}...")
        
        if not copyright_found:
            print(f"    ✓ No copyright content in early chunks (filtered out)")
        if not toc_found:
            print(f"    ✓ No TOC content in early chunks (filtered out)")
        
        print()
    
    print("=" * 80)
    print("VERIFICATION:")
    print("  Copyright/TOC pages should be excluded by boilerplate filter")
    print("  If not found in early chunks, filter is working correctly")
    print("=" * 80)
