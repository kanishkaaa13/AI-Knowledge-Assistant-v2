"""
Test error handling for corrupted file upload - simplified version
"""

import uuid
from pathlib import Path
from app.db.session import get_db
from app.models.user import User
from app.services.document_processor import DocumentProcessor
from fastapi import HTTPException

with next(get_db()) as db:
    user = db.query(User).filter(
        User.id == uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")
    ).first()
    
    print("Error Handling Test - Corrupted File Upload:")
    print("=" * 80)
    print()
    
    processor = DocumentProcessor()
    
    # Test 1: Corrupted PDF (invalid PDF header)
    print("Test 1: Corrupted PDF file (invalid header)")
    corrupted_pdf = b"This is not a PDF file at all"
    
    try:
        result = processor.process_document(
            db=db,
            user_id=user.id,
            title="Corrupted PDF Test",
            file_name="corrupted.pdf",
            file_bytes=corrupted_pdf,
            mime_type="application/pdf"
        )
        print(f"  ✗ FAIL: Upload succeeded when it should have failed")
    except HTTPException as e:
        print(f"  ✓ PASS: HTTPException raised")
        print(f"    Status Code: {e.status_code}")
        print(f"    Detail: {e.detail}")
    except Exception as e:
        print(f"  ⚠ Other exception: {type(e).__name__}: {e}")
    
    print()
    print("=" * 80)
