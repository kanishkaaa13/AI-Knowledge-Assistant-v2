"""
Check for any SQLite database locks or concurrent access.
"""

import sqlite3
from pathlib import Path

db_path = Path("ai_knowledge_assistant.db")
print(f"Database path: {db_path}")
print()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("SQLITE LOCK STATUS")
print("=" * 80)
print()

# Check for any active locks
try:
    cursor.execute("PRAGMA database_list")
    databases = cursor.fetchall()
    print(f"Databases: {databases}")
except Exception as e:
    print(f"Error checking databases: {e}")

# Try to get lock status
try:
    cursor.execute("PRAGMA lock_status")
    lock_status = cursor.fetchall()
    print(f"Lock status: {lock_status}")
except Exception as e:
    print(f"Error checking lock status: {e}")

# Check for busy timeout
try:
    cursor.execute("PRAGMA busy_timeout")
    busy_timeout = cursor.fetchone()[0]
    print(f"Busy timeout: {busy_timeout}ms")
except Exception as e:
    print(f"Error checking busy timeout: {e}")

# Check for any uncommitted transactions
try:
    cursor.execute("PRAGMA deferred_foreign_keys")
    deferred_fk = cursor.fetchone()[0]
    print(f"Deferred foreign keys: {deferred_fk}")
except Exception as e:
    print(f"Error checking deferred FK: {e}")

conn.close()

# Check for any lock files
lock_file = db_path.with_suffix(db_path.suffix + "-lock")
print()
print(f"Lock file exists: {lock_file.exists()}")
