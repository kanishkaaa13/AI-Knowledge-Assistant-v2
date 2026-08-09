"""
Investigate user 12b2f540-96bf-4b44-92da-f263524a8662 in detail.
Check user, documents, and chunks in SQL database.
"""

from app.db.session import get_db
from app.models.user import User
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk

import uuid

user_id = uuid.UUID("12b2f540-96bf-4b44-92da-f263524a8662")

with next(get_db()) as db:
    # Check user
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        print(f"User found:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.name}")
        print(f"  Created at: {user.created_at}")
        print(f"  Updated at: {user.updated_at}")
    else:
        print("User NOT found in database")
    
    print()
    
    # Check documents
    documents = db.query(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    print(f"Documents for user: {len(documents)}")
    for doc in documents:
        print(f"  - ID: {doc.id}")
        print(f"    Title: {doc.title}")
        print(f"    Filename: {doc.file_name}")
        print(f"    Status: {doc.status}")
        print(f"    Created at: {doc.created_at}")
    
    print()
    
    # Check chunks
    chunks = db.query(DocumentChunk).join(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    print(f"Chunks for user: {len(chunks)}")
    for chunk in chunks[:5]:  # Show first 5
        print(f"  - ID: {chunk.id}")
        print(f"    Document ID: {chunk.document_id}")
        print(f"    Content preview: {chunk.content[:100]}...")
    if len(chunks) > 5:
        print(f"  ... and {len(chunks) - 5} more chunks")
