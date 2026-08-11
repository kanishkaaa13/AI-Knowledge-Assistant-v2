"""
Dry run: Analyze existing chunks to see what would be flagged as boilerplate.
"""

import uuid
import re
from collections import Counter
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

def check_keyword_patterns(content: str) -> bool:
    """Check if content matches boilerplate keyword patterns (current live version)."""
    patterns = [
        r"table of contents",
        r"contents\s*\.\s*",  # "Contents . . ." pattern from TOC
        r"copyright\s*©",
        r"all rights reserved",
        r"isbn\s*\d",
        r"preface",  # More flexible - not standalone
        r"foreword",
        r"acknowledgments",
        r"page\s+[ivx]+\s*\.",  # Roman numeral pages with period
    ]
    content_lower = content.lower()
    for pattern in patterns:
        if re.search(pattern, content_lower):
            return True
    return False

def check_content_density(content: str) -> bool:
    """Check if content has low information density (revised - more conservative)."""
    # Very low unique-word density: < 10 unique words per 100 characters (was 20)
    words = content.split()
    unique_words = set(word.lower() for word in words if word.strip())
    
    if len(content) < 50:
        return True  # Too short
    
    unique_word_ratio = len(unique_words) / max(len(content), 1) * 100
    if unique_word_ratio < 10:  # < 10 unique words per 100 chars (was 20)
        return True
    
    # High repetition: > 30% of words repeated
    word_counts = Counter(word.lower() for word in words)
    repeated_words = sum(1 for count in word_counts.values() if count > 1)
    if len(words) > 0 and repeated_words / len(words) > 0.3:
        return True
    
    return False

def check_position_with_content(content: str, chunk_index: int, total_chunks: int) -> bool:
    """Check position heuristic only if combined with specific boilerplate keywords."""
    # Position alone is not enough - only triggers with specific boilerplate keywords
    if chunk_index < 2:  # First 2 chunks (was 3)
        return True
    if chunk_index >= total_chunks - 2:  # Last 2 chunks
        return True
    return False


def is_heading_pattern(content: str) -> bool:
    """Check if content matches heading/title patterns (should not be flagged as boilerplate)."""
    lines = content.strip().split('\n')
    first_line = lines[0].strip() if lines else ""
    
    # Markdown headers (# ## ###)
    if re.match(r'^#+\s+\S', first_line):
        return True
    
    # Numbered section headers (1.1, 2.3.4, etc.)
    if re.match(r'^\d+(\.\d+)*\s+[A-Z]', first_line):
        return True
    
    # Short lines that look like titles (all caps or title case, < 10 words)
    words = first_line.split()
    if len(words) <= 10 and len(words) >= 2:
        # All caps
        if first_line.isupper():
            return True
        # Title case (most words capitalized)
        capitalized_words = sum(1 for w in words if w[0].isupper())
        if capitalized_words / len(words) >= 0.7:
            return True
    
    return False

print("=" * 80)
print("BOILERPLATE DETECTION DRY RUN")
print("=" * 80)
print()

with next(get_db()) as db:
    documents = db.query(UploadedDocument).filter(UploadedDocument.user_id == user_id).all()
    
    total_chunks = 0
    flagged_chunks = 0
    
    for doc in documents:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index).all()
        total_chunks += len(chunks)
        
        print(f"Document: {doc.title}")
        print(f"  Filename: {doc.file_name}")
        print(f"  Total chunks: {len(chunks)}")
        print()
        
        for chunk in chunks:
            heuristics_triggered = []
            
            # Check each heuristic
            if check_keyword_patterns(chunk.content):
                heuristics_triggered.append("keyword")
            
            if check_content_density(chunk.content):
                heuristics_triggered.append("density")
            
            if check_position_with_content(chunk.content, chunk.chunk_index, len(chunks)):
                heuristics_triggered.append("position")
            
            # Mark as boilerplate if ANY of these trigger (revised logic):
            # 1. Specific boilerplate keyword match (copyright, TOC, etc.)
            # 2. Position (first 2 chunks) + specific boilerplate keyword
            # 3. Very low density (< 10 unique words/100 chars) + position (first/last 2 chunks) - but NOT for headings
            is_boilerplate = False
            
            if check_keyword_patterns(chunk.content):
                # Specific boilerplate keyword - always flag
                is_boilerplate = True
            elif check_position_with_content(chunk.content, chunk.chunk_index, len(chunks)):
                # Position only - need very low density to flag
                # Skip density-based flagging for headings/titles
                if is_heading_pattern(chunk.content):
                    is_boilerplate = False
                elif check_content_density(chunk.content):
                    is_boilerplate = True
            
            if is_boilerplate:
                flagged_chunks += 1
                content_preview = chunk.content[:150].replace('\n', ' ')
                print(f"  [FLAGGED] Chunk {chunk.chunk_index} (Page {chunk.page_number})")
                print(f"    Heuristics: {', '.join(heuristics_triggered)}")
                print(f"    Content: {content_preview}...")
                print()
        
        print("-" * 80)
        print()

print("=" * 80)
print(f"SUMMARY")
print("=" * 80)
print(f"Total chunks analyzed: {total_chunks}")
print(f"Chunks flagged as boilerplate: {flagged_chunks}")
print(f"Percentage: {flagged_chunks/total_chunks*100:.1f}%")
