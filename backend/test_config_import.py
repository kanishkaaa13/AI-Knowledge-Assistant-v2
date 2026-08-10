"""
Test that the config imports cleanly after removing CHROMA_COLLECTION_NAME.
"""

from app.core.config import settings

print("=" * 80)
print("CONFIG IMPORT TEST")
print("=" * 80)
print()

print("Settings loaded successfully:")
print(f"  CHROMA_PERSIST_DIRECTORY: {settings.CHROMA_PERSIST_DIRECTORY}")
print(f"  EMBEDDING_MODEL_NAME: {settings.EMBEDDING_MODEL_NAME}")
print(f"  RAG_CHUNK_SIZE: {settings.RAG_CHUNK_SIZE}")
print(f"  RAG_TOP_K: {settings.RAG_TOP_K}")

print()
print("✓ Config imports cleanly without CHROMA_COLLECTION_NAME")
