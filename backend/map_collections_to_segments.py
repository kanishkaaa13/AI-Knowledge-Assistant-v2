"""
Map ChromaDB collections to their segment directories via chroma.sqlite3.
This identifies which segment directories belong to which collections.
"""

import sqlite3
from pathlib import Path
from app.core.config import settings

chroma_db_path = Path(settings.CHROMA_PERSIST_DIRECTORY) / "chroma.sqlite3"
print(f"ChromaDB SQLite path: {chroma_db_path}")

conn = sqlite3.connect(str(chroma_db_path))
cursor = conn.cursor()

print("=" * 80)
print("COLLECTION TO SEGMENT MAPPING")
print("=" * 80)
print()

# Get all collections
cursor.execute("SELECT name, id FROM collections")
collections = cursor.fetchall()

print("Collections and their segments:")
for collection_name, collection_id in collections:
    print(f"\nCollection: {collection_name}")
    print(f"  ID: {collection_id}")
    
    # Get segments for this collection
    cursor.execute("SELECT id, type FROM segments WHERE collection = ?", (collection_id,))
    segments = cursor.fetchall()
    
    for seg_id, seg_type in segments:
        print(f"  Segment ID: {seg_id}")
        print(f"  Type: {seg_type}")
        
        # Check if segment directory exists
        segment_dir = Path(settings.CHROMA_PERSIST_DIRECTORY) / seg_id
        print(f"  Directory exists: {segment_dir.exists()}")
        if segment_dir.exists():
            print(f"  Directory path: {segment_dir}")

conn.close()
