"""
Test error handling for corrupted file upload
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
    
    # Test 1: Corrupted PDF (invalid PDF header)
    print("Test 1: Corrupted PDF file (invalid header)")
    corrupted_pdf = b"This is not a PDF file at all"
    
    processor = DocumentProcessor()
    
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
        print(f"  Result: {result}")
    except HTTPException as e:
        print(f"  ✓ PASS: HTTPException raised")
        print(f"    Status Code: {e.status_code}")
        print(f"    Detail: {e.detail}")
        if e.status_code == 422:
            print(f"    ✓ Correct status code (422)")
        else:
            print(f"    ✗ Wrong status code (expected 422, got {e.status_code})")
    except Exception as e:
        print(f"  ⚠ Other exception: {type(e).__name__}: {e}")
    
    print()
    
    # Test 2: Empty file
    print("Test 2: Empty file")
    empty_file = b""
    
    try:
        result = processor.process_document(
            db=db,
            user_id=user.id,
            title="Empty File Test",
            file_name="empty.pdf",
            file_bytes=empty_file,
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
    
    # Test 3: Valid PDF (should succeed)
    print("Test 3: Valid PDF file (control test)")
    valid_pdf = b"%PDF-1.7\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000202 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n299\n%%EOF"
    
    try:
        result = processor.process_document(
            db=db,
            user_id=user.id,
            title="Valid PDF Test",
            file_name="valid.pdf",
            file_bytes=valid_pdf,
            mime_type="application/pdf"
        )
        print(f"  ✓ PASS: Valid PDF uploaded successfully")
        print(f"    Document ID: {result.document_id}")
        # Clean up the test document
        from app.models.uploaded_document import UploadedDocument
        test_doc = db.query(UploadedDocument).filter(
            UploadedDocument.id == result.document_id
        ).first()
        if test_doc:
            # Delete the file
            file_path = Path(test_doc.file_path)
            if file_path.exists():
                file_path.unlink()
            # Delete the DB record
            db.delete(test_doc)
            db.commit()
            print(f"    Cleaned up test document")
    except Exception as e:
        print(f"  ✗ FAIL: Valid PDF upload failed: {e}")
    
    print()
    print("=" * 80)
