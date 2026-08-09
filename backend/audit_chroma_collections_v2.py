"""
Re-run orphan audit with SQL chunk counts as proxy for vector counts.
This bypasses the ChromaDB count() API error by using SQL data instead.
"""

import uuid
from pathlib import Path

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk

print("=" * 80)
print("ORPHANED COLLECTION AUDIT (WITH SQL CHUNK COUNTS)")
print("=" * 80)
print()

# Get all users from app database
users = {}
try:
    with next(get_db()) as db:
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
import sqlite3
chroma_db_path = Path(settings.CHROMA_PERSIST_DIRECTORY) / "chroma.sqlite3"

collections = []
try:
    conn = sqlite3.connect(str(chroma_db_path))
    cursor = conn.cursor()
    
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
print("DETAILED AUDIT RESULTS")
print("=" * 80)
print()

orphaned = []
valid = []

for collection in collections:
    collection_name = collection["name"]
    
    # Extract user_id from collection name
    user_id = None
    if collection_name.startswith("knowledge_chunks_"):
        user_id = collection_name.replace("knowledge_chunks_", "")
    elif collection_name.startswith("user_collection_"):
        user_id = collection_name.replace("user_collection_", "")
    
    if user_id:
        # Check if user exists in app database
        user_exists = user_id in users
        
        # Get SQL chunk count for this user
        sql_chunk_count = 0
        if user_exists:
            try:
                with next(get_db()) as db:
                    user_uuid = uuid.UUID(user_id)
                    chunks = db.query(DocumentChunk).join(UploadedDocument).filter(
                        UploadedDocument.user_id == user_uuid
                    ).all()
                    sql_chunk_count = len(chunks)
            except Exception as e:
                print(f"Error getting SQL chunk count: {e}")
        
        # Try ChromaDB count (may fail)
        chroma_count = "ERROR"
        try:
            import chromadb
            client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
            chroma_collections = client.list_collections()
            for col in chroma_collections:
                if col.name == collection_name:
                    try:
                        chroma_count = col.count()
                    except Exception:
                        chroma_count = "API_ERROR"
                    break
        except Exception:
            chroma_count = "API_ERROR"
        
        status = "VALID" if user_exists else "ORPHANED"
        
        print(f"Collection: {collection_name}")
        print(f"  User ID: {user_id}")
        print(f"  User exists: {user_exists}")
        if user_exists:
            print(f"  User email: {users[user_id]['email']}")
        print(f"  SQL chunk count: {sql_chunk_count}")
        print(f"  Chroma vector count: {chroma_count}")
        print(f"  Status: {status}")
        print()
        
        if user_exists:
            valid.append({
                "collection_name": collection_name,
                "user_id": user_id,
                "user_email": users[user_id]['email'],
                "sql_chunk_count": sql_chunk_count,
                "chroma_count": chroma_count,
            })
        else:
            orphaned.append({
                "collection_name": collection_name,
                "user_id": user_id,
                "sql_chunk_count": sql_chunk_count,
                "chroma_count": chroma_count,
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

if valid:
    print("VALID COLLECTIONS:")
    for item in valid:
        print(f"  - {item['collection_name']}")
        print(f"    User: {item['user_email']}")
        print(f"    SQL chunks: {item['sql_chunk_count']}")
        print(f"    Chroma vectors: {item['chroma_count']}")
    print()

if orphaned:
    print("ORPHANED COLLECTIONS:")
    for item in orphaned:
        print(f"  - {item['collection_name']} (user_id: {item['user_id']})")
        print(f"    SQL chunks: {item['sql_chunk_count']}")
        print(f"    Chroma vectors: {item['chroma_count']}")
