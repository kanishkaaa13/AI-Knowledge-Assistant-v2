import uuid
from pydantic import Field
from app.schemas.common import ORMBaseSchema, TimestampSchema

class OKFRecordRead(TimestampSchema):
    source_document_id: uuid.UUID
    file_path: str
    type: str
    title: str
    tags: list[str] = Field(default_factory=list)

class OKFRecordListResponse(ORMBaseSchema):
    items: list[OKFRecordRead]
    total: int
    page: int
    page_size: int
