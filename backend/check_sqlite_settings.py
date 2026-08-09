"""
Check SQLite WAL mode and journal settings for ai_knowledge_assistant.db.
"""

import sqlite3
from pathlib import Path

db_path = Path("ai_knowledge_assistant.db")
print(f"Database path: {db_path}")
print(f"File exists: {db_path.exists()}")
print()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("SQLITE DATABASE SETTINGS")
print("=" * 80)
print()

# Check journal mode
cursor.execute("PRAGMA journal_mode")
journal_mode = cursor.fetchone()[0]
print(f"Journal mode: {journal_mode}")

# Check WAL status
cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
wal_checkpoint = cursor.fetchone()
print(f"WAL checkpoint: {wal_checkpoint}")

# Check synchronous mode
cursor.execute("PRAGMA synchronous")
synchronous = cursor.fetchone()[0]
print(f"Synchronous mode: {synchronous}")

# Check locking mode
cursor.execute("PRAGMA locking_mode")
locking_mode = cursor.fetchone()[0]
print(f"Locking mode: {locking_mode}")

# Check cache size
cursor.execute("PRAGMA cache_size")
cache_size = cursor.fetchone()[0]
print(f"Cache size: {cache_size}")

# Check page size
cursor.execute("PRAGMA page_size")
page_size = cursor.fetchone()[0]
print(f"Page size: {page_size}")

# Check for WAL file
wal_file = db_path.with_suffix(db_path.suffix + "-wal")
shm_file = db_path.with_suffix(db_path.suffix + "-shm")
print()
print(f"WAL file exists: {wal_file.exists()}")
print(f"WAL file size: {wal_file.stat().st_size if wal_file.exists() else 'N/A'}")
print(f"SHM file exists: {shm_file.exists()}")
print(f"SHM file size: {shm_file.stat().st_size if shm_file.exists() else 'N/A'}")

conn.close()
