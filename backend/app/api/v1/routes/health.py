from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
    }


@router.get("/health/ollama")
async def ollama_health_check() -> dict[str, str]:
    import httpx
    from app.services.ollama_llm import OllamaLLMService
    service = OllamaLLMService()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(service.base_url)
            response.raise_for_status()
        return {"status": "ok", "model": settings.OLLAMA_DEFAULT_MODEL}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/debug/chroma")
async def debug_chroma() -> dict:
    """
    Diagnostic endpoint: shows how many vectors are stored per user collection.
    """
    import os
    from pathlib import Path
    from app.services.vector_store import get_vector_store_service

    persist_dir = settings.CHROMA_PERSIST_DIRECTORY
    dir_exists = Path(persist_dir).exists()
    dir_absolute = str(Path(persist_dir).resolve())

    # Ensure directory exists
    os.makedirs(persist_dir, exist_ok=True)

    vs = get_vector_store_service()
    try:
        all_collections = vs.client.list_collections()
        collection_info = []
        for col in all_collections:
            try:
                c = vs.client.get_collection(col.name)
                count = c.count()
                sample_metadata: dict = {}
                sample_ids: list = []
                if count > 0:
                    # peek() returns a dict with lists: ids, documents, metadatas, embeddings
                    peeked = c.peek(limit=1)
                    raw_meta = peeked.get("metadatas") or []
                    if raw_meta and isinstance(raw_meta, list) and len(raw_meta) > 0:
                        first = raw_meta[0]
                        # ChromaDB may return list-of-dicts or just a dict
                        if isinstance(first, dict):
                            sample_metadata = first
                        elif isinstance(first, list) and len(first) > 0:
                            sample_metadata = first[0]
                    raw_ids = peeked.get("ids") or []
                    sample_ids = raw_ids[:3] if raw_ids else []
                collection_info.append({
                    "name": col.name,
                    "total_vectors": count,
                    "sample_ids": sample_ids,
                    "sample_metadata_keys": list(sample_metadata.keys()),
                    "sample_metadata": sample_metadata,
                })
            except Exception as e:
                collection_info.append({"name": col.name, "error": str(e)})

        return {
            "persist_directory": persist_dir,
            "persist_directory_absolute": dir_absolute,
            "persist_directory_exists": dir_exists,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "total_collections": len(all_collections),
            "collections": collection_info,
        }
    except Exception as exc:
        import traceback
        return {
            "persist_directory": persist_dir,
            "persist_directory_absolute": dir_absolute,
            "persist_directory_exists": dir_exists,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
