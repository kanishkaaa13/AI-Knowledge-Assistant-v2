"""
Delete the corrupted ChromaDB collections from storage/chroma (authoritative path).
"""

import chromadb
from app.core.config import settings

print("=" * 80)
print("DELETING CORRUPTED COLLECTIONS FROM storage/chroma")
print(f"Path: {settings.CHROMA_PERSIST_DIRECTORY}")
print("=" * 80)
print()

client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)

# Collections to delete
collections_to_delete = [
    "user_collection_12b2f540-96bf-4b44-92da-f263524a8662",
    "user_collection_2f9c2a2c-2dac-4596-b117-6b2cffe01425",
]

for collection_name in collections_to_delete:
    print(f"Deleting collection: {collection_name}")
    try:
        client.delete_collection(collection_name)
        print(f"  ✓ Collection deleted")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    print()

print("=" * 80)
print("DELETION COMPLETE")
print("=" * 80)
