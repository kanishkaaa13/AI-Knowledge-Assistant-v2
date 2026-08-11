"""
Test decryption on all PDFs for this user
"""

import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.core.crypto import encryption_service
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

with next(get_db()) as db:
    documents = db.query(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    
    print(f"Testing {len(documents)} documents:")
    print()
    
    for doc in documents:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"  Created: {doc.created_at}")
        
        file_path = Path(doc.file_path)
        if not file_path.exists():
            print(f"  ✗ File not found")
            print()
            continue
        
        raw_bytes = file_path.read_bytes()
        print(f"  File size: {len(raw_bytes)} bytes")
        
        # Try decryption
        try:
            decrypted = encryption_service.decrypt_bytes(raw_bytes)
            print(f"  ✓ Decryption successful (file is encrypted)")
        except Exception as e:
            print(f"  ✗ Decryption failed: {type(e).__name__}")
            
            # Check if it's unencrypted PDF
            try:
                reader = PdfReader(BytesIO(raw_bytes))
                print(f"  ✓ File is unencrypted PDF (pypdf can read it)")
                print(f"    PDF pages: {len(reader.pages)}")
            except Exception as pdf_err:
                print(f"  ✗ Not a valid PDF: {pdf_err}")
        
        print()
