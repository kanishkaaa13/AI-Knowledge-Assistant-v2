"""
Check the uploaded document from the API test
"""

import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.core.crypto import encryption_service

with next(get_db()) as db:
    # Find the most recently uploaded document
    doc = db.query(UploadedDocument).filter(
        UploadedDocument.title == "API Test Document"
    ).order_by(UploadedDocument.created_at.desc()).first()
    
    print("Checking Uploaded Document from API Test:")
    print("=" * 80)
    print()
    
    if doc:
        print(f"Document: {doc.title}")
        print(f"  ID: {doc.id}")
        print(f"  File: {doc.file_name}")
        print(f"  File path: {doc.file_path}")
        print(f"  Page count: {doc.page_count}")
        print()
        
        # Read raw bytes from disk
        disk_path = Path(doc.file_path)
        if disk_path.exists():
            raw_bytes = disk_path.read_bytes()
            print(f"File size: {len(raw_bytes)} bytes")
            print(f"First 50 bytes (hex): {raw_bytes[:50].hex()}")
            print()
            
            # Check if it's a valid PDF
            try:
                reader = PdfReader(BytesIO(raw_bytes))
                print(f"✗ File is valid PDF (NOT encrypted)")
            except Exception as pdf_err:
                print(f"✓ File is NOT valid PDF (encrypted)")
                print(f"  Error: {pdf_err}")
            
            print()
            
            # Try to decrypt
            try:
                decrypted = encryption_service.decrypt_bytes(raw_bytes)
                print(f"✓ Decryption successful")
                print(f"  Decrypted size: {len(decrypted)} bytes")
                
                # Verify it's a valid PDF after decryption
                reader = PdfReader(BytesIO(decrypted))
                print(f"✓ Decrypted file is valid PDF with {len(reader.pages)} pages")
                print()
                
                # Show page content
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    print(f"  Page {i+1}: {text[:100]}...")
            except Exception as decrypt_err:
                print(f"✗ Decryption failed: {decrypt_err}")
        else:
            print(f"✗ File not found on disk: {doc.file_path}")
    else:
        print("✗ Document not found in database")
    
    print()
    print("=" * 80)
