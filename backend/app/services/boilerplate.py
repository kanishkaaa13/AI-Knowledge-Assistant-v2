"""Shared heuristics for detecting boilerplate chunks (TOC, copyright pages, ...)."""

from __future__ import annotations

import re
from collections import Counter

BOILERPLATE_PATTERNS = (
    r"table of contents",
    r"contents\s*\.\s*",  # "Contents . . ." pattern from a TOC
    r"copyright\s*©",
    r"all rights reserved",
    r"isbn\s*\d",
    r"preface",
    r"foreword",
    r"acknowledgments",
    r"page\s+[ivx]+\s*\.",  # roman numeral pages followed by a period
)

MIN_CONTENT_LENGTH = 50
MIN_UNIQUE_WORD_RATIO = 10  # unique words per 100 characters
MAX_REPEATED_WORD_RATIO = 0.3
EDGE_CHUNK_COUNT = 2


def check_keyword_patterns(content: str) -> bool:
    """Check if content matches boilerplate keyword patterns."""
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in BOILERPLATE_PATTERNS)


def check_content_density(content: str) -> bool:
    """Check if content has low information density."""
    if len(content) < MIN_CONTENT_LENGTH:
        return True

    words = content.split()
    unique_words = {word.lower() for word in words if word.strip()}

    unique_word_ratio = len(unique_words) / max(len(content), 1) * 100
    if unique_word_ratio < MIN_UNIQUE_WORD_RATIO:
        return True

    word_counts = Counter(word.lower() for word in words)
    repeated_words = sum(1 for count in word_counts.values() if count > 1)
    return bool(words) and repeated_words / len(words) > MAX_REPEATED_WORD_RATIO


def check_position_with_content(chunk_index: int, total_chunks: int) -> bool:
    """Check whether the chunk sits at the leading or trailing edge of a document."""
    return chunk_index < EDGE_CHUNK_COUNT or chunk_index >= total_chunks - EDGE_CHUNK_COUNT


def is_heading_pattern(content: str) -> bool:
    """Check if content looks like a heading/title, which is never boilerplate."""
    lines = content.strip().split("\n")
    first_line = lines[0].strip() if lines else ""

    # Markdown headers (# ## ###)
    if re.match(r"^#+\s+\S", first_line):
        return True

    # Numbered section headers (1.1, 2.3.4, ...)
    if re.match(r"^\d+(\.\d+)*\s+[A-Z]", first_line):
        return True

    words = first_line.split()
    if 2 <= len(words) <= 10:
        if first_line.isupper():
            return True
        capitalized_words = sum(1 for word in words if word[0].isupper())
        if capitalized_words / len(words) >= 0.7:
            return True

    return False


def is_boilerplate_chunk(content: str, chunk_index: int, total_chunks: int) -> bool:
    """Determine whether a chunk should be dropped as boilerplate."""
    if check_keyword_patterns(content):
        return True

    if check_position_with_content(chunk_index, total_chunks):
        if is_heading_pattern(content):
            return False
        return check_content_density(content)

    return False
