import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.repositories.document import DocumentRepository


def get_owned_document(
    db: Session,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> UploadedDocument:
    """Fetch a document belonging to the user, or raise 404."""
    document = DocumentRepository(db).get_by_user(document_id, user_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return document


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    try:
        # Check cookie first
        token = request.cookies.get("access_token")
        
        # Fallback to Authorization header
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            )

        subject = payload["sub"]
        
        if getattr(request.state, "user_id", None) and request.state.user_id != subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication context mismatch.",
            )

        user_uuid = uuid.UUID(subject)
        user = db.get(User, user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
            
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions directly
        raise
    except Exception:
        # Catch any other parsing/DB errors and return 401 instead of crashing
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
