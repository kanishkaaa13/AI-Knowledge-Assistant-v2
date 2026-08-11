"""
Check what the StoredDocumentParser actually returns for this document
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.services.document_parser import StoredDocumentParser

document_id = uuid.UUID("7488d639-ab79-4eb3-b809-06ab42e157b8")

with next(get_db()) as db:
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if doc:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"DB page_count: {doc.page_count}")
        print(f"Extracted text length: {len(doc.extracted_text or '')} chars")
        print()
        
        parser = StoredDocumentParser()
        pages = parser.parse(doc)
        
        print(f"Parser returned {len(pages)} pages")
        print()
        
        if len(pages) > 0:
            print("First 3 pages from parser:")
            for i, page in enumerate(pages[:3]):
                print(f"  Page {page.page_number}: {len(page.text)} chars")
                preview = page.text[:100].replace('\n', ' ')
                print(f"    Preview: {preview}...")
                print()
            
            if len(pages) > 1:
                print(f"Page distribution:")
                for i, page in enumerate(pages):
                    if i < 5 or i >= len(pages) - 2:
                        print(f"  Page {page.page_number}: {len(page.text)} chars")
                    elif i == 5:
                        print(f"  ... ({len(pages) - 10} pages omitted) ...")
        else:
            print("Parser returned empty list - fallback would create single page from extracted_text")
