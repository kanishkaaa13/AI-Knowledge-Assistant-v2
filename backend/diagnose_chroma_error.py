"""
Diagnose ChromaDB internal error (type mismatch in metadata).
Attempt to get vector counts and capture full error details.
"""

from app.core.config import settings
from pathlib import Path
import chromadb

print("=" * 80)
print("CHROMADB ERROR DIAGNOSIS")
print("=" * 80)
print()

print(f"ChromaDB persist directory: {settings.CHROMA_PERSIST_DIRECTORY}")
print(f"Directory exists: {Path(settings.CHROMA_PERSIST_DIRECTORY).exists()}")
print()

client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)

print("Attempting to list collections...")
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
            print("  Full stack trace:")
            import traceback
            traceback.print_exc()
            print()
        
        print()
        
except Exception as e:
    print(f"Error listing collections: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("CHECKING CHROMADB SQLITE METADATA")
print("=" * 80)
print()

import sqlite3

chroma_db_path = Path(settings.CHROMA_PERSIST_DIRECTORY) / "chroma.sqlite3"
print(f"ChromaDB SQLite path: {chroma_db_path}")
print(f"File exists: {chroma_db_path.exists()}")
print()

try:
    conn = sqlite3.connect(str(chroma_db_path))
    cursor = conn.cursor()
    
    # Check collections table schema
    print("Collections table schema:")
    cursor.execute("PRAGMA table_info(collections)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col}")
    print()
    
    # Check segments table schema
    print("Segments table schema:")
    cursor.execute("PRAGMA table_info(segments)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col}")
    print()
    
    # Check for metadata column type issues
    print("Sample collection data:")
    cursor.execute("SELECT name, id FROM collections LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")
    print()
    
    conn.close()
    
except Exception as e:
    print(f"Error reading ChromaDB SQLite: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
