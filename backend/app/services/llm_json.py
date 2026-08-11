"""Helpers for recovering JSON payloads from raw LLM output."""

from __future__ import annotations

import re


def extract_json_block(text: str) -> str:
    """Isolate the JSON substring of an LLM response, if one can be located."""
    text = text.strip()

    # 1. Fenced block explicitly tagged as json
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 2. Any fenced block
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 3. First array or object literal
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text
