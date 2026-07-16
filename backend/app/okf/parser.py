import yaml
import re
from .schema import OKFDocument

def parse_okf(raw_text: str) -> OKFDocument:
    """
    Parses a raw text document in OKF (Open Knowledge Format).
    It splits the YAML frontmatter (between --- markers) from the markdown body,
    parses the YAML using PyYAML, and validates it against OKFDocument.
    """
    # Normalize line endings
    normalized_text = raw_text.replace("\r\n", "\n")
    
    # Match frontmatter block at the start of the file
    pattern = r"^\s*---\s*\n(.*?)\n---\s*\n?(.*)$"
    match = re.match(pattern, normalized_text, re.DOTALL)
    
    if not match:
        raise ValueError("Invalid OKF format: Missing frontmatter or delimiters")
        
    frontmatter_yaml = match.group(1)
    body = match.group(2)
    
    try:
        data = yaml.safe_load(frontmatter_yaml) or {}
    except Exception as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")
        
    if not isinstance(data, dict):
        raise ValueError("Invalid OKF format: Frontmatter is not a valid YAML dictionary")
        
    # Inject body for validation
    data["body"] = body
    
    return OKFDocument.model_validate(data)

def serialize_okf(doc: OKFDocument) -> str:
    """
    Serializes an OKFDocument back into a raw text string with YAML frontmatter
    and markdown body.
    """
    # Extract metadata fields for frontmatter, excluding body
    data = doc.model_dump(exclude={"body"})
    
    # safe_dump preserves python types like datetime, list, etc.
    # sort_keys=False keeps the order defined in the Pydantic schema
    yaml_str = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    
    return f"---\n{yaml_str}---\n{doc.body}"
