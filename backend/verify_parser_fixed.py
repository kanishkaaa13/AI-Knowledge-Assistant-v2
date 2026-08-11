"""
Verify StoredDocumentParser reads through fixed encryption path with real page counts
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.services.document_parser import StoredDocumentParser

with next(get_db()) as db:
    # Test one document
    doc = db.query(UploadedDocument).filter(
        UploadedDocument.title == "machine-learning-cheat-sheet"
    ).first()
    
    print("Verifying StoredDocumentParser with fixed encryption:")
    print("=" * 80)
    print()
    
    print(f"Document: {doc.title}")
    print(f"  DB page_count: {doc.page_count}")
    print()
    
    parser = StoredDocumentParser()
    
    try:
        pages = parser.parse(doc)
        print(f"✓ Parser succeeded")
        print(f"  Pages returned: {len(pages)}")
        print(f"  Page numbers: {[p.page_number for p in pages[:10]]}... (first 10)")
        
        if len(pages) == doc.page_count:
            print(f"✓ Page count matches DB: {len(pages)} == {doc.page_count}")
        else:
            print(f"✗ Page count mismatch: {len(pages)} != {doc.page_count}")
        
        # Check if page numbers are sequential from 1
        expected_pages = list(range(1, len(pages) + 1))
        actual_pages = [p.page_number for p in pages]
        if actual_pages == expected_pages:
            print(f"✓ Page numbers are sequential from 1")
        else:
            print(f"✗ Page numbers are not sequential")
            print(f"  Expected: {expected_pages[:10]}...")
            print(f"  Actual: {actual_pages[:10]}...")
            
    except Exception as e:
        print(f"✗ Parser failed: {e}")
    
    print()
    print("=" * 80)
