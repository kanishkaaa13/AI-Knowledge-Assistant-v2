"""
Check documents for user 2f9c2a2c to find the one with page 16.
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

with next(get_db()) as db:
    documents = db.query(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    
    print(f"User {user_id} has {len(documents)} documents:")
    for doc in documents:
        print(f"  - {doc.title} ({doc.file_name})")
        print(f"    Pages: {doc.page_count}")
        print(f"    ID: {doc.id}")
        print()
