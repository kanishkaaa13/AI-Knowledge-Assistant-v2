"""
Check the extracted_text field to see if it contains multi-page content
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument

document_id = uuid.UUID("7488d639-ab79-4eb3-b809-06ab42e157b8")

with next(get_db()) as db:
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if doc:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"DB page_count: {doc.page_count}")
        print(f"Extracted text length: {len(doc.extracted_text or '')} chars")
        print()
        
        # Count occurrences of page markers in extracted text
        text = doc.extracted_text or ""
        
        # Look for common page markers
        page_markers = [
            "Page 16",
            "page 16",
            "p. 16",
            "1.1 Types of machine learning",
        ]
        
        print("Searching for page markers in extracted text:")
        for marker in page_markers:
            count = text.lower().count(marker.lower())
            if count > 0:
                print(f"  '{marker}': found {count} times")
                # Find context
                idx = text.lower().find(marker.lower())
                if idx >= 0:
                    start = max(0, idx - 50)
                    end = min(len(text), idx + 100)
                    context = text[start:end].replace('\n', ' ')
                    print(f"    Context: ...{context}...")
            else:
                print(f"  '{marker}': not found")
        
        print()
        print("First 500 chars of extracted text:")
        print(text[:500].replace('\n', ' '))
        print()
        print("Last 500 chars of extracted text:")
        print(text[-500:].replace('\n', ' '))
