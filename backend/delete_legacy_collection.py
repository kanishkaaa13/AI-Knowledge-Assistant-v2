"""
Delete the legacy knowledge_chunks_12b2f540-96bf-4b44-92da-f263524a8662 collection.
"""

import chromadb
from app.core.config import settings

print("=" * 80)
print("DELETING LEGACY KNOWLEDGE_CHUNKS COLLECTION")
print(f"Path: {settings.CHROMA_PERSIST_DIRECTORY}")
print("=" * 80)
print()

client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)

collection_name = "knowledge_chunks_12b2f540-96bf-4b44-92da-f263524a8662"

print(f"Deleting collection: {collection_name}")
try:
    client.delete_collection(collection_name)
    print(f"  ✓ Collection deleted successfully")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("DELETION COMPLETE")
print("=" * 80)
