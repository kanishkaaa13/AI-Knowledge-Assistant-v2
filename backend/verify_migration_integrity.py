"""
Verify content integrity of migrated files by comparing extracted text
"""

import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.services.document_parser import StoredDocumentParser

with next(get_db()) as db:
    documents = db.query(UploadedDocument).all()
    
    print(f"Verifying content integrity for {len(documents)} migrated files:")
    print()
    
    parser = StoredDocumentParser()
    
    all_match = True
    
    for doc in documents:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"  DB extracted_text length: {len(doc.extracted_text or '')} chars")
        
        try:
            # Parse the re-encrypted file
            pages = parser.parse(doc)
            
            if not pages:
                print(f"  ✗ No pages parsed")
                all_match = False
                continue
            
            # Extract text from parsed pages
            current_extracted = "\n".join(page.text for page in pages)
            print(f"  Current extracted text length: {len(current_extracted)} chars")
            
            # Compare with stored extracted_text
            if doc.extracted_text:
                if current_extracted == doc.extracted_text:
                    print(f"  ✓ Extracted text matches exactly")
                else:
                    # Check if it's close (allowing for minor extraction differences)
                    similarity = len(current_extracted) / max(len(doc.extracted_text), 1)
                    print(f"  ⚠ Extracted text differs (similarity: {similarity:.2%})")
                    
                    # Show first difference
                    for i, (c1, c2) in enumerate(zip(doc.extracted_text, current_extracted)):
                        if c1 != c2:
                            print(f"    First difference at position {i}:")
                            print(f"      DB: {repr(doc.extracted_text[max(0,i-20):i+20])}")
                            print(f"      Current: {repr(current_extracted[max(0,i-20):i+20])}")
                            break
                    
                    all_match = False
            else:
                print(f"  ⚠ No stored extracted_text to compare")
        except Exception as e:
            print(f"  ✗ Failed to parse: {e}")
            all_match = False
        
        print()
    
    print("=" * 80)
    if all_match:
        print("✓ All files verified - content integrity preserved")
    else:
        print("✗ Some files have content integrity issues")
    print("=" * 80)
