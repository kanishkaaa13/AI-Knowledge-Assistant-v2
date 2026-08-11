"""
Verify that re-encrypted files can be read correctly
"""

import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.services.document_parser import StoredDocumentParser

with next(get_db()) as db:
    # Check the PDFs that were re-encrypted
    documents = db.query(UploadedDocument).filter(
        UploadedDocument.file_extension == ".pdf"
    ).all()
    
    print(f"Testing {len(documents)} re-encrypted PDF documents:")
    print()
    
    parser = StoredDocumentParser()
    
    for doc in documents:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"  Created: {doc.created_at}")
        
        try:
            pages = parser.parse(doc)
            print(f"  ✓ Successfully parsed {len(pages)} pages")
            
            # Verify page content
            if pages:
                print(f"  First page text length: {len(pages[0].text)} chars")
                preview = pages[0].text[:100].replace('\n', ' ')
                print(f"  Preview: {preview}...")
        except Exception as e:
            print(f"  ✗ Failed to parse: {e}")
        
        print()
