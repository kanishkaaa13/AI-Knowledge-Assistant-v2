import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.services.ollama_llm import OllamaLLMService

logger = logging.getLogger(__name__)


def extract_json_block(text: str) -> str:
    """
    Tries to isolate a JSON substring from the LLM output.
    """
    text = text.strip()
    # 1. Match code blocks starting with ```json
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 2. Match generic code blocks starting with ```
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 3. Match first array [ ... ] or object { ... }
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def split_text_into_sections(text: str) -> list[dict]:
    """
    Splits text into logical sections based on Markdown heading structure.
    If fewer than 2 headings are found, it falls back to grouping paragraphs.
    """
    lines = text.splitlines()
    sections = []
    current_title = "Introduction"
    current_lines = []
    
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
    
    for line in lines:
        match = heading_pattern.match(line.strip())
        if match:
            if current_lines:
                sections.append({
                    "title": current_title,
                    "content": "\n".join(current_lines).strip()
                })
            current_title = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
            
    if current_lines:
        sections.append({
            "title": current_title,
            "content": "\n".join(current_lines).strip()
        })
        
    # If we got at least 2 sections, use this header-based splitting
    if len(sections) >= 2:
        return [s for s in sections if s["content"].strip()]
        
    # Fallback: Split by paragraph blocks
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    sections = []
    current_p_group = []
    current_char_count = 0
    section_index = 1
    
    for p in paragraphs:
        current_p_group.append(p)
        current_char_count += len(p)
        
        # Split when the paragraph group reaches ~1500 chars, or 4 paragraphs
        if current_char_count >= 1500 or len(current_p_group) >= 4:
            content = "\n\n".join(current_p_group)
            first_line = current_p_group[0].split(".")[0].strip()
            title = first_line[:50] + "..." if len(first_line) > 50 else first_line
            sections.append({
                "title": f"Section {section_index}: {title}",
                "content": content
            })
            section_index += 1
            current_p_group = []
            current_char_count = 0
            
    if current_p_group:
        content = "\n\n".join(current_p_group)
        first_line = current_p_group[0].split(".")[0].strip()
        title = first_line[:50] + "..." if len(first_line) > 50 else first_line
        sections.append({
            "title": f"Section {section_index}: {title}",
            "content": content
        })
        
    return [s for s in sections if s["content"].strip()]


class OKFConverterService:
    """
    Standalone service to convert extracted text from a document into an Open Knowledge Format (OKF) bundle.
    """
    
    def __init__(self) -> None:
        self.llm = OllamaLLMService()

    async def _generate_metadata(self, section_title: str, section_content: str) -> dict:
        """
        Uses the default LLM to generate a clean title, description (one-line summary), and tags for the section.
        """
        prompt = (
            "You are an expert AI knowledge indexing assistant.\n"
            "Your task is to analyze the provided section of a document and extract metadata to represent it in a knowledge catalog.\n\n"
            "Analyze the content below and return a JSON object with the following fields:\n"
            "- title: A refined, concise, and clean descriptive title representing this content (e.g., 'Introduction to FastAPI' or 'Rate Limiting Policy').\n"
            "- description: A clear, one-line summary (maximum 20 words) detailing what this section is about.\n"
            "- tags: A list of 3 to 5 relevant keyword tags representing the concepts in this content.\n\n"
            f"Suggested original title: {section_title}\n"
            f"Content snippet (first 1500 chars):\n{section_content[:1500]}\n\n"
            "Return ONLY a valid JSON object. Do not wrap it in any dialogue, extra comments, or introductory text. "
            "Ensure the output keys are exactly 'title', 'description', and 'tags'."
        )
        
        try:
            raw_response = await self.llm.generate(prompt=prompt, model=settings.DEFAULT_CHAT_MODEL)
            cleaned_json = extract_json_block(raw_response)
            metadata = json.loads(cleaned_json)
            
            # Basic validation
            title = metadata.get("title", section_title).strip()
            description = metadata.get("description", "").strip()
            tags = metadata.get("tags", [])
            if not isinstance(tags, list):
                tags = [str(tags)]
                
            return {
                "title": title or section_title,
                "description": description or "Summary of section.",
                "tags": [str(t).strip() for t in tags if t]
            }
        except Exception as e:
            logger.warning("LLM metadata extraction failed for section '%s': %s", section_title, e)
            return {
                "title": section_title,
                "description": f"Content section starting with: {section_content[:60]}...",
                "tags": ["General"]
            }

    async def convert_to_okf_bundle(self, document_id: str, document_title: str, text: str) -> Path:
        """
        Converts the document's extracted text into an OKF catalog bundle.
        Writes one markdown file per logical section, plus an index.md table of contents.
        Returns the path to the output bundle directory.
        """
        # Define output directory under backend/okf_bundles/<document_id>
        backend_dir = Path(__file__).resolve().parent.parent.parent
        bundle_dir = backend_dir / "okf_bundles" / document_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        
        sections = split_text_into_sections(text)
        if not sections:
            raise ValueError("Document text could not be split into any logical sections.")
            
        logger.info("Converting document %s (%s) into OKF bundle containing %s sections", 
                    document_id, document_title, len(sections))
        
        concepts_manifest = []
        now_str = datetime.now().isoformat()
        
        for idx, sec in enumerate(sections, start=1):
            title = sec["title"]
            content = sec["content"]
            
            # Generate metadata using the default LLM
            meta = await self._generate_metadata(title, content)
            refined_title = meta["title"]
            description = meta["description"]
            tags = meta["tags"]
            
            # Make a safe, clean filename
            safe_title = re.sub(r"[^A-Za-z0-9_-]+", "-", refined_title).strip("-").lower()
            filename = f"{idx:03d}-{safe_title or 'section'}.md"
            filepath = bundle_dir / filename
            
            # Format YAML frontmatter
            yaml_header = (
                "---\n"
                "type: concept\n"
                f"title: {json.dumps(refined_title)}\n"
                f"description: {json.dumps(description)}\n"
                f"tags: {json.dumps(tags)}\n"
                f"timestamp: \"{now_str}\"\n"
                "---\n\n"
            )
            
            filepath.write_text(yaml_header + content, encoding="utf-8")
            
            concepts_manifest.append({
                "filename": filename,
                "title": refined_title,
                "description": description,
                "tags": tags
            })
            
        # Write root index.md listing all concept files
        index_content = (
            f"# OKF Knowledge Catalog: {document_title}\n\n"
            f"This bundle is generated in Open Knowledge Format (OKF) from the document: `{document_title}`.\n\n"
            "## Concepts Index\n\n"
            "| File | Title | Description | Tags |\n"
            "| :--- | :--- | :--- | :--- |\n"
        )
        for item in concepts_manifest:
            tags_str = ", ".join([f"`{t}`" for t in item["tags"]])
            index_content += f"| [{item['filename']}]({item['filename']}) | {item['title']} | {item['description']} | {tags_str} |\n"
            
        index_filepath = bundle_dir / "index.md"
        index_filepath.write_text(index_content, encoding="utf-8")
        
        logger.info("OKF bundle successfully created at %s", bundle_dir)
        return bundle_dir
