from datetime import datetime
from pydantic import BaseModel, Field

class OKFDocument(BaseModel):
    type: str = Field(..., description="The type of document, e.g. concept, api, policy, dataset")
    title: str
    tags: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list, description="slugs/filenames of related OKF documents")
    source_document_id: str | None = None
    created_at: datetime
    updated_at: datetime
    body: str = Field(..., description="The markdown content below the frontmatter")
