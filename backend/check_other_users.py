"""
Check PDF encryption status for other users
"""

import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.core.crypto import encryption_service
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.user import User

with next(get_db()) as db:
    # Check the other user with PDFs
    users = db.query(User).filter(User.id == uuid.UUID("12b2f540-96bf-4b44-92da-f263524a8662")).all()
    
    print(f"Checking {len(users)} other users:")
    print()
    
    for user in users:
        print(f"User: {user.email} ({user.id})")
        
        documents = db.query(UploadedDocument).filter(
            UploadedDocument.user_id == user.id,
            UploadedDocument.file_extension == ".pdf"
        ).limit(2).all()
        
        if not documents:
            print("  No PDF documents found")
            print()
            continue
        
        for doc in documents:
            print(f"  Document: {doc.title} ({doc.file_name})")
            print(f"    Created: {doc.created_at}")
            
            file_path = Path(doc.file_path)
            if not file_path.exists():
                print(f"    ✗ File not found")
                continue
            
            raw_bytes = file_path.read_bytes()
            print(f"    File size: {len(raw_bytes)} bytes")
            
            # Try decryption
            try:
                decrypted = encryption_service.decrypt_bytes(raw_bytes)
                print(f"    ✓ Decryption successful (file is encrypted)")
            except Exception as e:
                print(f"    ✗ Decryption failed: {type(e).__name__}")
                
                # Check if it's unencrypted PDF
                try:
                    reader = PdfReader(BytesIO(raw_bytes))
                    print(f"    ✓ File is unencrypted PDF (pypdf can read it)")
                    print(f"      PDF pages: {len(reader.pages)}")
                except Exception as pdf_err:
                    print(f"    ✗ Not a valid PDF: {pdf_err}")
        
        print()
