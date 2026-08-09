"""
Get vector counts using ChromaDB API get() method instead of count().
This bypasses the count() API error.
"""

from app.core.config import settings
from pathlib import Path
import chromadb

print("=" * 80)
print("VECTOR COUNTS USING CHROMADB API get() METHOD")
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
            # Use get() with limit=0 to get count without fetching data
            result = col.get(limit=0, include=[])
            if result and 'ids' in result:
                count = len(result['ids'])
                print(f"  Vector count: {count}")
            else:
                print(f"  Vector count: 0 (empty result)")
        except Exception as e:
            print(f"  ERROR using get(): {type(e).__name__}: {e}")
        
        print()
        
except Exception as e:
    print(f"Error listing collections: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
