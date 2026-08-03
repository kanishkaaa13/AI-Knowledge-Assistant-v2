import os
import re
import json
import logging
from pathlib import Path
import yaml

from app.core.config import settings
from app.services.ollama_llm import OllamaLLMService

logger = logging.getLogger(__name__)

# Pattern to find Markdown links to other concept markdown files (e.g., [Link](002-screenshots.md))
LINK_PATTERN = re.compile(r"\[.*?\]\((.*?\.md)\)")


def parse_concept_file(filepath: Path) -> tuple[dict, str]:
    """
    Parses a concept markdown file. Splits the YAML frontmatter from the markdown body.
    Returns (metadata_dict, body_text).
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to read concept file %s: %s", filepath, exc)
        return {}, ""
        
    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter_text = parts[1]
        body = parts[2].strip()
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            if isinstance(frontmatter, dict):
                return frontmatter, body
        except Exception as exc:
            logger.warning("Failed to parse YAML frontmatter in %s: %s", filepath.name, exc)
            
    return {}, content.strip()


def keyword_match(query: str, concepts: list[dict]) -> list[tuple[float, dict]]:
    """
    Performs simple keyword overlapping scoring between the query and concept metadata.
    Returns a list of tuples: (score, concept_data) sorted by score descending.
    """
    # Clean query into lower-case keywords
    query_words = set(re.findall(r"\w+", query.lower()))
    if not query_words:
        return []
        
    results = []
    for concept in concepts:
        meta = concept["metadata"]
        title = meta.get("title", "").lower()
        desc = meta.get("description", "").lower()
        tags = [str(t).lower() for t in meta.get("tags", [])]
        
        score = 0.0
        
        # Tokenize and score overlaps
        title_words = set(re.findall(r"\w+", title))
        desc_words = set(re.findall(r"\w+", desc))
        
        # Exact keyword in title: high weight
        title_overlap = len(query_words.intersection(title_words))
        score += title_overlap * 3.0
        
        # Exact keyword in tags: medium weight
        tags_overlap = len(query_words.intersection(set(tags)))
        score += tags_overlap * 2.0
        
        # Exact keyword in description: low weight
        desc_overlap = len(query_words.intersection(desc_words))
        score += desc_overlap * 1.0
        
        if score > 0:
            results.append((score, concept))
            
    # Sort by score descending
    results.sort(key=lambda item: item[0], reverse=True)
    return results


async def llm_match(query: str, concepts: list[dict]) -> list[str]:
    """
    Fallback method: Sends all concept metadata to the LLM to choose relevant filenames.
    Returns a list of matching filenames.
    """
    llm = OllamaLLMService()
    
    # Format metadata catalog for the LLM
    catalog = []
    for c in concepts:
        meta = c["metadata"]
        catalog.append({
            "filename": c["filename"],
            "title": meta.get("title", ""),
            "description": meta.get("description", ""),
            "tags": meta.get("tags", [])
        })
        
    prompt = (
        "You are an AI search assistant.\n"
        "Your task is to select which concept files from the provided knowledge catalog are relevant to the user's query.\n\n"
        f"USER QUERY: \"{query}\"\n\n"
        "KNOWLEDGE CATALOG:\n"
        f"{json.dumps(catalog, indent=2)}\n\n"
        "Instructions:\n"
        "1. Identify the concept files that contain information relevant to answering the user query.\n"
        "2. Return ONLY a valid JSON list of filenames (e.g., [\"001-introduction.md\", \"004-core-features.md\"]).\n"
        "3. Do not include any other explanations, notes, or markdown wraps in your response."
    )
    
    try:
        raw_response = await llm.generate(prompt=prompt, model=settings.DEFAULT_CHAT_MODEL)
        
        # Clean response to isolate JSON array
        cleaned = raw_response.strip()
        match = re.search(r"(\[.*\])", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
            
        filenames = json.loads(cleaned)
        if isinstance(filenames, list):
            return [str(f).strip() for f in filenames]
    except Exception as exc:
        logger.error("LLM fallback matching failed: %s", exc)
        
    return []


def follow_links(selected_filenames: list[str], all_concepts_dict: dict[str, dict], bundle_dir: Path) -> list[str]:
    """
    Implements one-hop link-following. Finds markdown links within the bodies of the
    selected files and appends the linked concept files if they exist in the bundle.
    """
    final_filenames = list(selected_filenames)
    linked_filenames = []
    
    for filename in selected_filenames:
        concept = all_concepts_dict.get(filename)
        if not concept:
            continue
            
        body = concept["body"]
        # Find all .md file links
        matches = LINK_PATTERN.findall(body)
        for match in matches:
            linked_name = os.path.basename(match)
            if linked_name in all_concepts_dict and linked_name not in final_filenames and linked_name not in linked_filenames:
                linked_filenames.append(linked_name)
                
    # Add one-hop link follow results
    final_filenames.extend(linked_filenames)
    return final_filenames


class OKFRetrieverService:
    """
    Service to retrieve relevant concept files from an OKF bundle.
    """
    
    async def retrieve_concepts(self, bundle_path_str: str, query: str) -> list[dict]:
        bundle_path = Path(bundle_path_str)
        if not bundle_path.exists() or not bundle_path.is_dir():
            raise FileNotFoundError(f"OKF bundle directory not found at: {bundle_path_str}")
            
        # 1. Load and parse all concept markdown files (excluding index.md)
        concepts = []
        concepts_dict = {}
        
        for file in bundle_path.glob("*.md"):
            if file.name.lower() == "index.md":
                continue
                
            metadata, body = parse_concept_file(file)
            if not metadata:
                continue
                
            concept_data = {
                "filename": file.name,
                "metadata": metadata,
                "body": body,
                "filepath": str(file.resolve())
            }
            concepts.append(concept_data)
            concepts_dict[file.name] = concept_data
            
        if not concepts:
            logger.warning("No valid concept files found in bundle %s", bundle_path_str)
            return []
            
        # 2. Try simple keyword/tag matching
        scored_matches = keyword_match(query, concepts)
        
        # Threshold: We want at least 2 relevant matches. If not, fallback to LLM.
        selected_filenames = []
        retrieval_method = "keyword"
        
        if len(scored_matches) >= 2:
            # Take top matches (e.g. limit to top 4 scored matches)
            selected_filenames = [item[1]["filename"] for item in scored_matches[:4]]
            logger.info("Retrieved %s concepts using keyword matching", len(selected_filenames))
        else:
            # 3. Fallback to LLM semantic matching
            logger.info("Keyword matches below threshold (%s found). Falling back to LLM matcher...", len(scored_matches))
            selected_filenames = await llm_match(query, concepts)
            retrieval_method = "llm_fallback"
            
            # If LLM fallback failed or returned nothing, return keyword matches as a last resort
            if not selected_filenames and scored_matches:
                selected_filenames = [item[1]["filename"] for item in scored_matches]
                retrieval_method = "keyword_fallback"
                
        # 4. Follow links (one-hop traversal)
        all_retrieved_filenames = follow_links(selected_filenames, concepts_dict, bundle_path)
        
        # 5. Hydrate final payload
        results = []
        for filename in all_retrieved_filenames:
            concept = concepts_dict.get(filename)
            if concept:
                is_link_followed = filename not in selected_filenames
                results.append({
                    "filename": concept["filename"],
                    "title": concept["metadata"].get("title", ""),
                    "description": concept["metadata"].get("description", ""),
                    "tags": concept["metadata"].get("tags", []),
                    "body": concept["body"],
                    "filepath": concept["filepath"],
                    "retrieved_via": "link_follow" if is_link_followed else retrieval_method
                })
                
        return results
