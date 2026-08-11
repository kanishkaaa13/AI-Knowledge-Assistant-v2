"""
Find users with PDF documents
"""

from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from sqlalchemy import func

with next(get_db()) as db:
    # Get user IDs that have PDF documents
    result = db.query(
        UploadedDocument.user_id,
        func.count(UploadedDocument.id).label('pdf_count')
    ).filter(
        UploadedDocument.file_extension == ".pdf"
    ).group_by(UploadedDocument.user_id).all()
    
    print(f"Users with PDF documents:")
    for user_id, count in result:
        print(f"  User ID: {user_id}, PDF count: {count}")
