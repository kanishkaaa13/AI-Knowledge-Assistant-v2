"""
Investigate encryption failure for PDF documents
"""

import uuid
from pathlib import Path
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

with next(get_db()) as db:
    documents = db.query(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    
    print(f"User has {len(documents)} documents:")
    print()
    
    for doc in documents:
        print(f"Document: {doc.title} ({doc.file_name})")
        print(f"  File path: {doc.file_path}")
        print(f"  File exists: {Path(doc.file_path).exists() if doc.file_path else 'N/A'}")
        print(f"  File size: {Path(doc.file_path).stat().st_size if doc.file_path and Path(doc.file_path).exists() else 'N/A'} bytes")
        print(f"  Created at: {doc.created_at}")
        print(f"  Status: {doc.status}")
        print(f"  Processing error: {doc.processing_error}")
        print()
