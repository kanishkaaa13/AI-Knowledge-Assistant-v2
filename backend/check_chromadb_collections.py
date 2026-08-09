"""
Check ChromaDB collections in storage/chromadb (where reindexing actually wrote).
"""

import chromadb
from pathlib import Path

chromadb_path = Path("storage/chromadb")
print(f"ChromaDB path: {chromadb_path}")
print(f"Directory exists: {chromadb_path.exists()}")

client = chromadb.PersistentClient(path=str(chromadb_path))

print("=" * 80)
print("COLLECTIONS IN storage/chromadb")
print("=" * 80)
print()

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
