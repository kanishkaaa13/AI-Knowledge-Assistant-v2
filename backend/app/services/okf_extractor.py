import json
import logging
import re
from datetime import datetime
from app.okf.schema import OKFDocument
from app.services.ollama_llm import OllamaLLMService
from app.core.config import settings

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

async def extract_okf_concepts(document_text: str, source_document_id: str) -> list[OKFDocument]:
    """
    Analyzes document text using the LLM to extract distinct OKF concepts.
    Returns a list of successfully validated OKFDocument objects.
    """
    prompt = (
        "You are an AI knowledge extraction assistant. Your task is to analyze the following document text "
        "and extract distinct, self-contained concepts, entities, APIs, policies, or topics as Open Knowledge Format (OKF) documents.\n\n"
        "For each distinct concept identified in the text, you must return a structured object with the following fields:\n"
        "- type: A string categorizing the concept (e.g., 'concept', 'api', 'policy', 'dataset', 'class', 'function', 'topic').\n"
        "- title: A clear, descriptive title for the concept.\n"
        "- tags: A list of relevant keywords or categorization tags.\n"
        "- related: A list of names or titles of related concepts that are mentioned or closely linked to this concept.\n"
        "- body: A clean, descriptive markdown summary detailing the concept.\n\n"
        "Output ONLY a valid JSON array of objects representing these concepts. Do not include any conversational intro/outro text. Make sure the JSON is valid and parsable.\n\n"
        "Here is the document text to extract from:\n"
        "------------------\n"
        f"{document_text}\n"
        "------------------\n\n"
        "JSON output:"
    )

    ollama = OllamaLLMService()
    try:
        model = settings.DEFAULT_CHAT_MODEL
        raw_response = await ollama.generate(prompt=prompt, model=model)
    except Exception as e:
        logger.exception("LLM generation failed during OKF extraction")
        raise RuntimeError(f"LLM generation failed: {str(e)}")

    cleaned_json = extract_json_block(raw_response)
    try:
        concepts_data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM response. Raw response: {raw_response}. Error: {e}")
        return []

    if not isinstance(concepts_data, list):
        if isinstance(concepts_data, dict):
            concepts_data = [concepts_data]
        else:
            logger.error(f"Parsed JSON is not a list or dictionary: {concepts_data}")
            return []

    okf_documents = []
    now = datetime.now()

    for item in concepts_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping malformed concept item (not a dict): {item}")
            continue

        # Inject standard required fields
        item["source_document_id"] = source_document_id
        item["created_at"] = item.get("created_at", now)
        item["updated_at"] = item.get("updated_at", now)

        try:
            doc = OKFDocument.model_validate(item)
            okf_documents.append(doc)
        except Exception as e:
            logger.warning(f"Skipping concept item due to validation error: {e}. Item: {item}")
            continue

    return okf_documents
