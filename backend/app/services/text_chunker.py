import re
from collections import Counter
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
    is_boilerplate: bool = False


def check_keyword_patterns(content: str) -> bool:
    """Check if content matches boilerplate keyword patterns."""
    patterns = [
        r"table of contents",
        r"^contents\s*$",
        r"copyright\s*©",
        r"all rights reserved",
        r"isbn\s*\d",
        r"^preface\s*$",
        r"^foreword\s*$",
        r"^acknowledgments\s*$",
        r"page\s+[ivx]+",
    ]
    content_lower = content.lower()
    for pattern in patterns:
        if re.search(pattern, content_lower):
            return True
    return False


def check_content_density(content: str) -> bool:
    """Check if content has low information density."""
    words = content.split()
    unique_words = set(word.lower() for word in words if word.strip())
    
    if len(content) < 50:
        return True  # Too short
    
    unique_word_ratio = len(unique_words) / max(len(content), 1) * 100
    if unique_word_ratio < 10:  # < 10 unique words per 100 chars
        return True
    
    # High repetition: > 30% of words repeated
    word_counts = Counter(word.lower() for word in words)
    repeated_words = sum(1 for count in word_counts.values() if count > 1)
    if len(words) > 0 and repeated_words / len(words) > 0.3:
        return True
    
    return False


def check_position_with_content(chunk_index: int, total_chunks: int) -> bool:
    """Check position heuristic only if combined with specific boilerplate keywords."""
    if chunk_index < 2:  # First 2 chunks
        return True
    if chunk_index >= total_chunks - 2:  # Last 2 chunks
        return True
    return False


def is_boilerplate_chunk(content: str, chunk_index: int, total_chunks: int) -> bool:
    """Determine if a chunk is boilerplate using revised detection logic."""
    # Specific boilerplate keyword - always flag
    if check_keyword_patterns(content):
        return True
    
    # Position only - need very low density to flag
    if check_position_with_content(chunk_index, total_chunks):
        if check_content_density(content):
            return True
    
    return False


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

        # Apply boilerplate detection and filter
        total_chunks = len(chunked_documents)
        filtered_chunks = []
        new_index = 0
        
        for chunk in chunked_documents:
            is_boilerplate = is_boilerplate_chunk(chunk.content, chunk.chunk_index, total_chunks)
            if not is_boilerplate:
                # Re-index the chunk after filtering
                chunk.chunk_index = new_index
                chunk.is_boilerplate = False
                filtered_chunks.append(chunk)
                new_index += 1
        
        return filtered_chunks
