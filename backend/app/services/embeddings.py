# backend/app/services/embeddings.py
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

_embedding_fn = None

def get_embedding_model():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = DefaultEmbeddingFunction()
        print("[STARTUP] ChromaDB DefaultEmbeddingFunction loaded")
    return _embedding_fn

def get_embedding(texts: list[str]) -> list:
    model = get_embedding_model()
    return model(texts)
