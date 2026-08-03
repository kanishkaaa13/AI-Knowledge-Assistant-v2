import chromadb
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings

print(f"ChromaDB persist directory: {settings.CHROMA_PERSIST_DIRECTORY}")
print(f"Directory exists: {Path(settings.CHROMA_PERSIST_DIRECTORY).exists()}")

client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)

print("\n=== All ChromaDB Collections ===")
try:
    collections = client.list_collections()
    print(f"Total collections: {len(collections)}")
    for col in collections:
        print(f"  - {col.name} (count: {col.count()})")
except Exception as e:
    print(f"Error listing collections: {e}")
    import traceback
    traceback.print_exc()
