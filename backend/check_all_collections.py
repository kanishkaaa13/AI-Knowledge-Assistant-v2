"""
Check all ChromaDB collections including the ones we just reindexed.
"""

import chromadb
from app.core.config import settings

print("=" * 80)
print("ALL CHROMADB COLLECTIONS")
print("=" * 80)
print()

client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)

try:
    collections = client.list_collections()
    print(f"Total collections: {len(collections)}")
    print()
    
    for col in collections:
        print(f"Collection: {col.name}")
        print(f"  ID: {col.id}")
        
        try:
            count = col.count()
            print(f"  Vector count: {count}")
        except Exception as e:
            print(f"  ERROR getting count: {type(e).__name__}: {e}")
        
        print()
        
except Exception as e:
    print(f"Error listing collections: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
