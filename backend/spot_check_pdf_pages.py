"""
Spot-check 2 documents against actual PDF page numbers
"""

import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk
from app.core.crypto import encryption_service

with next(get_db()) as db:
    # Test 2 specific documents
    test_docs = [
        "machine-learning-cheat-sheet",
        "Unit 3"
    ]
    
    print("Spot-checking PDF page numbers:")
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
        
        # Read and decrypt the actual PDF
        file_path = Path(doc.file_path)
        encrypted_bytes = file_path.read_bytes()
        decrypted_bytes = encryption_service.decrypt_bytes(encrypted_bytes)
        
        # Get actual PDF page count
        reader = PdfReader(BytesIO(decrypted_bytes))
        actual_page_count = len(reader.pages)
        print(f"  Actual PDF page count: {actual_page_count}")
        
        # Get chunk page numbers
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).order_by(DocumentChunk.chunk_index).all()
        
        chunk_page_numbers = [chunk.page_number for chunk in chunks]
        unique_chunk_pages = sorted(set(chunk_page_numbers))
        
        print(f"  Chunks: {len(chunks)}")
        print(f"  Unique chunk page numbers: {unique_chunk_pages}")
        print(f"  Chunk page range: {min(unique_chunk_pages)} - {max(unique_chunk_pages)}")
        
        # Verify page numbers are within actual PDF range
        if all(1 <= p <= actual_page_count for p in unique_chunk_pages):
            print(f"  ✓ All chunk page numbers are within PDF range (1-{actual_page_count})")
        else:
            print(f"  ✗ Some chunk page numbers are outside PDF range")
            invalid_pages = [p for p in unique_chunk_pages if p < 1 or p > actual_page_count]
            print(f"    Invalid pages: {invalid_pages}")
        
        # Check specific known content
        if doc_name == "machine-learning-cheat-sheet":
            # Look for "Types of machine learning" content
            for chunk in chunks:
                if "Types of machine learning" in chunk.content.lower() or "supervised" in chunk.content.lower():
                    print(f"  ✓ Found 'Types of machine learning' or 'supervised' content:")
                    print(f"    Chunk {chunk.chunk_index}: Page {chunk.page_number}")
                    preview = chunk.content[:100].replace('\n', ' ')
                    print(f"    Content: {preview}...")
                    break
        
        print()
    
    print("=" * 80)
