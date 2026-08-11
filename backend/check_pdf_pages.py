"""
Check actual PDF page count vs what's being parsed
"""

import uuid
from io import BytesIO
from pypdf import PdfReader
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.services.document_upload import read_encrypted_document_bytes

document_id = uuid.UUID("7488d639-ab79-4eb3-b809-06ab42e157b8")

with next(get_db()) as db:
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if doc:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"DB page_count: {doc.page_count}")
        print()
        
        try:
            file_bytes = read_encrypted_document_bytes(doc)
            reader = PdfReader(BytesIO(file_bytes))
            print(f"Actual PDF page count (pypdf): {len(reader.pages)}")
            print()
            
            # Show first few pages with their text length
            print("First 5 pages (text length):")
            for i in range(min(5, len(reader.pages))):
                page = reader.pages[i]
                text = page.extract_text() or ""
                print(f"  Page {i+1}: {len(text)} chars")
                if len(text) > 0:
                    preview = text[:100].replace('\n', ' ')
                    print(f"    Preview: {preview}...")
                print()
            
            # Check page 16 specifically
            if len(reader.pages) >= 16:
                page_16 = reader.pages[15]  # 0-indexed
                text_16 = page_16.extract_text() or ""
                print(f"Page 16 text length: {len(text_16)} chars")
                if "Types of machine learning" in text_16 or "types of machine learning" in text_16.lower():
                    print("  Contains 'Types of machine learning'")
                    preview = text_16[:200].replace('\n', ' ')
                    print(f"  Preview: {preview}...")
                else:
                    print("  Does NOT contain 'Types of machine learning'")
                    preview = text_16[:200].replace('\n', ' ')
                    print(f"  Preview: {preview}...")
        except Exception as e:
            print(f"Error reading PDF: {e}")
            import traceback
            traceback.print_exc()
