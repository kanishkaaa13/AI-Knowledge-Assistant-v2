from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.document_parser import ParsedDocumentPage


@dataclass
class ChunkedPageDocument:
    page_number: int | None
    chunk_index: int
    content: str
    metadata: dict


class DocumentChunker:
    def __init__(self) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        )

    def chunk_text(self, *, text: str, metadata: dict) -> list[Document]:
        source_document = Document(page_content=text, metadata=metadata)
        return self.splitter.split_documents([source_document])

    def chunk_pages(self, *, pages: list[ParsedDocumentPage], metadata: dict) -> list[ChunkedPageDocument]:
        chunked_documents: list[ChunkedPageDocument] = []
        running_index = 0

        for page in pages:
            if not page.text.strip():
                continue

            split_docs = self.chunk_text(
                text=page.text,
                metadata={**metadata, "page": page.page_number},
            )
            for split_doc in split_docs:
                chunked_documents.append(
                    ChunkedPageDocument(
                        page_number=page.page_number,
                        chunk_index=running_index,
                        content=split_doc.page_content,
                        metadata=split_doc.metadata,
                    )
                )
                running_index += 1

        return chunked_documents
