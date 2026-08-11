"""
Test decryption directly on file bytes to diagnose the issue
"""

import uuid
from pathlib import Path
from app.core.crypto import encryption_service
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument

# Test with one of the older PDFs (Unit 4 - uploaded May 29)
document_id = uuid.UUID("3741ded2-b8d8-472e-9181-37c8594a279a")

with next(get_db()) as db:
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if doc:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"  Created: {doc.created_at}")
        print(f"  File path: {doc.file_path}")
        print()
        
        file_path = Path(doc.file_path)
        if file_path.exists():
            raw_bytes = file_path.read_bytes()
            print(f"Raw file size: {len(raw_bytes)} bytes")
            print(f"First 50 bytes (hex): {raw_bytes[:50].hex()}")
            print()
            
            try:
                decrypted = encryption_service.decrypt_bytes(raw_bytes)
                print(f"✓ Decryption successful")
                print(f"Decrypted size: {len(decrypted)} bytes")
                print(f"First 100 bytes: {decrypted[:100]}")
            except Exception as e:
                print(f"✗ Decryption failed: {e}")
                print(f"Error type: {type(e).__name__}")
                
                # Check if it's already unencrypted
                try:
                    # Try to read as PDF directly
                    from pypdf import PdfReader
                    from io import BytesIO
                    reader = PdfReader(BytesIO(raw_bytes))
                    print(f"✓ File appears to be unencrypted (pypdf can read it directly)")
                    print(f"  PDF pages: {len(reader.pages)}")
                except Exception as pdf_err:
                    print(f"✗ File is not a valid PDF either: {pdf_err}")
