"""
Audit Chroma collections for orphaned user collections.
This script lists all Chroma collections and checks if corresponding SQL users exist.
"""

import sqlite3
import uuid
from pathlib import Path

from app.core.config import settings
from app.db.session import get_db

# ChromaDB SQLite path
chroma_db_path = Path(settings.CHROMA_PERSIST_DIRECTORY) / "chroma.sqlite3"
app_db_path = Path("ai_knowledge_assistant.db")

print(f"ChromaDB path: {chroma_db_path}")
print(f"App DB path: {app_db_path}")
print()

# Get all users from app database
users = {}
try:
    with next(get_db()) as db:
        from app.models.user import User
        all_users = db.query(User).all()
        for user in all_users:
            users[str(user.id)] = {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
            }
    print(f"Found {len(users)} users in app database")
except Exception as e:
    print(f"Error reading app database: {e}")
    import traceback
    traceback.print_exc()

# Get all collections from ChromaDB SQLite directly
collections = []
try:
    conn = sqlite3.connect(str(chroma_db_path))
    cursor = conn.cursor()
    
    # Query collections table
    cursor.execute("SELECT name, id FROM collections")
    rows = cursor.fetchall()
    
    for row in rows:
        collection_name, collection_id = row
        collections.append({
            "name": collection_name,
            "id": collection_id,
        })
    
    conn.close()
    print(f"Found {len(collections)} collections in ChromaDB")
except Exception as e:
    print(f"Error reading ChromaDB: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("ORPHANED COLLECTION AUDIT")
print("=" * 80)
print()

orphaned = []
valid = []

for collection in collections:
    collection_name = collection["name"]
    
    # Extract user_id from collection name if it follows the pattern
    user_id = None
    if collection_name.startswith("knowledge_chunks_"):
        user_id = collection_name.replace("knowledge_chunks_", "")
    elif collection_name.startswith("user_collection_"):
        user_id = collection_name.replace("user_collection_", "")
    
    if user_id:
        # Check if user exists in app database
        user_exists = user_id in users
        
        status = "VALID" if user_exists else "ORPHANED"
        
        print(f"Collection: {collection_name}")
        print(f"  User ID: {user_id}")
        print(f"  User exists: {user_exists}")
        if user_exists:
            print(f"  User email: {users[user_id]['email']}")
        print(f"  Status: {status}")
        print()
        
        if user_exists:
            valid.append({
                "collection_name": collection_name,
                "user_id": user_id,
                "user_email": users[user_id]['email'],
            })
        else:
            orphaned.append({
                "collection_name": collection_name,
                "user_id": user_id,
            })
    else:
        print(f"Collection: {collection_name}")
        print(f"  Status: SYSTEM (no user_id)")
        print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total collections: {len(collections)}")
print(f"Valid collections (user exists): {len(valid)}")
print(f"Orphaned collections (user missing): {len(orphaned)}")
print()

if orphaned:
    print("ORPHANED COLLECTIONS:")
    for item in orphaned:
        print(f"  - {item['collection_name']} (user_id: {item['user_id']})")
