import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.okf_record import OKFRecord
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.okf.parser import parse_okf
from app.okf.schema import OKFDocument
from app.schemas.okf import OKFRecordListResponse

router = APIRouter()

@router.get("", response_model=OKFRecordListResponse)
async def list_okf_records(
    type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OKFRecordListResponse:
    """
    List all OKFRecord entries for the current user.
    Supports filtering by type and tags, and page-based pagination.
    """
    # Join with UploadedDocument to filter by current user's ownership
    stmt = select(OKFRecord).join(UploadedDocument).where(UploadedDocument.user_id == current_user.id)
    
    if type:
        stmt = stmt.where(OKFRecord.type == type)
        
    if tag:
        # Use LIKE mapping for JSON tags array query in SQLite/Postgres
        stmt = stmt.where(OKFRecord.tags.like(f'%"{tag}"%'))
        
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0
    
    # Sort and paginate
    stmt = stmt.order_by(OKFRecord.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    records = db.scalars(stmt).all()
    
    return OKFRecordListResponse(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
    )

@router.get("/{record_id}", response_model=OKFDocument)
async def get_okf_document(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OKFDocument:
    """
    Retrieve the full OKF document including its frontmatter metadata and parsed body content.
    The document file is read from the disk and validated using the parse_okf parser.
    """
    # Verify ownership before accessing the record
    stmt = select(OKFRecord).join(UploadedDocument).where(
        OKFRecord.id == record_id,
        UploadedDocument.user_id == current_user.id
    )
    record = db.scalar(stmt)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OKF Record not found."
        )
        
    # Resolve file path
    backend_dir = Path(__file__).resolve().parents[2]
    file_path = backend_dir / record.file_path
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OKF document file not found on disk."
        )
        
    try:
        raw_text = file_path.read_text(encoding="utf-8")
        doc = parse_okf(raw_text)
        return doc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse OKF document: {str(e)}"
        )
