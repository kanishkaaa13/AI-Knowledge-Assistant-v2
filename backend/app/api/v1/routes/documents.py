import uuid
from io import BytesIO

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import apply_rate_limit
from app.core.sanitize import ensure_present, sanitize_text
from app.db.session import get_db
from app.models.user import User
from app.models.uploaded_document import UploadedDocument
from app.repositories.document import DocumentRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentMetadataUpdate,
    DocumentPreviewRead,
    UploadedDocumentListItem,
    UploadedDocumentRead,
)
from app.services.background_jobs import process_document_ingestion
from app.services.document_upload import (
    create_document_record,
    delete_document_file,
    parse_upload,
    preview_text,
    read_encrypted_document_bytes,
)
from app.services.rag_pipeline import RAGIngestionService

router = APIRouter()


def parse_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [item.strip() for item in tags.split(",") if item.strip()]


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    search: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    favorites_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    repository = DocumentRepository(db)
    safe_search = sanitize_text(search, max_length=255) if search else None
    safe_tag = sanitize_text(tag, max_length=64) if tag else None
    documents = repository.list_by_user(
        current_user.id,
        page=page,
        page_size=page_size,
        search=safe_search,
        tag=safe_tag,
        favorites_only=favorites_only,
    )
    total = repository.count_filtered_by_user(
        current_user.id,
        search=safe_search,
        tag=safe_tag,
        favorites_only=favorites_only,
    )
    return DocumentListResponse(
        items=[
            UploadedDocumentListItem(
                **UploadedDocumentRead.model_validate(document).model_dump(),
                preview_text=preview_text(document.extracted_text),
                parsed_tags=parse_tags(document.tags),
            )
            for document in documents
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/upload", response_model=UploadedDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadedDocumentRead:
    apply_rate_limit(
        request,
        scope="documents-upload",
        limit=5,
        user_id=str(current_user.id),
    )
    safe_title = ensure_present(sanitize_text(title, max_length=255), field_name="title")
    
    from app.services.document_processor import DocumentProcessor
    
    try:
        from app.core.config import settings
        print(f"[UPLOAD] Received file: {file.filename}, size: {file.size}")
        print(f"[UPLOAD] User: {current_user.id}")
        print(f"[UPLOAD] Storage path: {settings.UPLOAD_ROOT_DIR}")

        processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        file_bytes = await file.read()
        
        processed = processor.process_document(
            db=db,
            user_id=current_user.id,
            title=safe_title or file.filename or "Document",
            file_name=file.filename or "document",
            file_bytes=file_bytes,
            mime_type=file.content_type,
        )

        document = db.get(UploadedDocument, processed.document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document record not found after processing.",
            )

        try:
            RAGIngestionService(db).index_document(document)
        except Exception as e:
            print(f"[INDEX ERROR] {e}")
            document.status = "pending"
            db.add(document)
            db.commit()
            db.refresh(document)

        return UploadedDocumentRead.model_validate(document)
    except Exception as e:
        import traceback
        print(f"[UPLOAD ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=UploadedDocumentRead)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadedDocumentRead:
    repository = DocumentRepository(db)
    document = repository.get_by_user(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return UploadedDocumentRead.model_validate(document)


@router.patch("/{document_id}/metadata", response_model=UploadedDocumentRead)
async def update_document_metadata(
    document_id: uuid.UUID,
    payload: DocumentMetadataUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadedDocumentRead:
    repository = DocumentRepository(db)
    document = repository.get_by_user(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    cleaned_tags = sorted({sanitize_text(tag, max_length=32).lower() for tag in payload.tags if tag.strip()})
    document.tags = ",".join(cleaned_tags) if cleaned_tags else None
    if payload.is_favorite is not None:
        document.is_favorite = payload.is_favorite
    db.add(document)
    db.commit()
    db.refresh(document)
    return UploadedDocumentRead.model_validate(document)


@router.get("/{document_id}/preview", response_model=DocumentPreviewRead)
async def get_document_preview(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentPreviewRead:
    repository = DocumentRepository(db)
    document = repository.get_by_user(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return DocumentPreviewRead(
        id=document.id,
        title=document.title,
        file_name=document.file_name,
        file_extension=document.file_extension,
        mime_type=document.mime_type,
        file_size=document.file_size,
        page_count=document.page_count,
        word_count=document.word_count,
        preview_text=preview_text(document.extracted_text),
        ai_summary=document.ai_summary,
        parsed_tags=parse_tags(document.tags),
        is_favorite=document.is_favorite,
    )


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    repository = DocumentRepository(db)
    document = repository.get_by_user(document_id, current_user.id)
    if not document or not document.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    file_bytes = read_encrypted_document_bytes(document)
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type=document.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{document.file_name}"'},
    )


@router.post("/{document_id}/reindex", response_model=UploadedDocumentRead)
async def reindex_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadedDocumentRead:
    repository = DocumentRepository(db)
    document = repository.get_by_user(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    print(f"[REINDEX] Starting reindex for doc {document.id} ({document.file_name!r})")
    print(f"[REINDEX] Extracted text length: {len(document.extracted_text or '')} chars")
    print(f"[REINDEX] User: {current_user.id}")

    try:
        chunks = RAGIngestionService(db).index_document(document)
        print(f"[REINDEX] Storing {len(chunks)} chunks for doc {document_id}")
        print(f"[REINDEX] Complete [OK]")
    except Exception as e:
        import traceback
        print(f"[REINDEX ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Reindex failed: {e}")

    db.refresh(document)
    return UploadedDocumentRead.model_validate(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    repository = DocumentRepository(db)
    document = repository.get_by_user(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    delete_document_file(document)
    RAGIngestionService(db).delete_document_index(document.id)
    repository.delete(document)
    return {"message": "Document deleted successfully."}
