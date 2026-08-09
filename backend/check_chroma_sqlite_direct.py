"""
Check ChromaDB SQLite directly to see all collections.
"""

import sqlite3
from pathlib import Path
from app.core.config import settings

chroma_db_path = Path(settings.CHROMA_PERSIST_DIRECTORY) / "chroma.sqlite3"
print(f"ChromaDB SQLite path: {chroma_db_path}")

conn = sqlite3.connect(str(chroma_db_path))
cursor = conn.cursor()

print("=" * 80)
print("COLLECTIONS IN CHROMADB SQLITE")
print("=" * 80)
print()

cursor.execute("SELECT name, id FROM collections")
rows = cursor.fetchall()

print(f"Total collections in SQLite: {len(rows)}")
print()

for row in rows:
    collection_name, collection_id = row
    print(f"Collection: {collection_name}")
    print(f"  ID: {collection_id}")

conn.close()
