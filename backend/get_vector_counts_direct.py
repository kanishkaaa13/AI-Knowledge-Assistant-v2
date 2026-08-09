"""
Get vector counts directly from ChromaDB SQLite to bypass the count() API error.
"""

import sqlite3
from pathlib import Path
from app.core.config import settings

chroma_db_path = Path(settings.CHROMA_PERSIST_DIRECTORY) / "chroma.sqlite3"
print(f"ChromaDB SQLite path: {chroma_db_path}")

conn = sqlite3.connect(str(chroma_db_path))
cursor = conn.cursor()

print("=" * 80)
print("VECTOR COUNTS FROM CHROMADB SQLITE (DIRECT)")
print("=" * 80)
print()

# Get all collections
cursor.execute("SELECT name, id FROM collections")
collections = cursor.fetchall()

for collection_name, collection_id in collections:
    print(f"Collection: {collection_name}")
    print(f"  ID: {collection_id}")
    
    # Try to get segment info
    try:
        cursor.execute("SELECT id, type FROM segments WHERE collection = ?", (collection_id,))
        segments = cursor.fetchall()
        print(f"  Segments: {len(segments)}")
        
        for seg_id, seg_type in segments:
            print(f"    - {seg_id}: {seg_type}")
            
            # Try to get row count from segment tables
            try:
                # ChromaDB creates tables like segment_<id>
                table_name = f"segment_{seg_id}"
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                print(f"      Rows: {row_count}")
            except Exception as e:
                print(f"      Error counting rows: {e}")
                
    except Exception as e:
        print(f"  Error getting segments: {e}")
    
    print()

conn.close()
