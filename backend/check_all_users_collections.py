"""
Check all users in the database and see if any have knowledge_chunks_* collections.
"""

import chromadb
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

print("=" * 80)
print("ALL USERS IN DATABASE")
print("=" * 80)
print()

with next(get_db()) as db:
    users = db.query(User).all()
    print(f"Total users: {len(users)}")
    print()
    
    for user in users:
        print(f"User: {user.email}")
        print(f"  ID: {user.id}")
        print()

print("=" * 80)
print("ALL CHROMADB COLLECTIONS")
print("=" * 80)
print()

client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
collections = client.list_collections()

print(f"Total collections: {len(collections)}")
print()

knowledge_chunks_collections = [col for col in collections if col.name.startswith("knowledge_chunks_")]
user_collections = [col for col in collections if col.name.startswith("user_collection_")]

print(f"knowledge_chunks_* collections: {len(knowledge_chunks_collections)}")
for col in knowledge_chunks_collections:
    print(f"  - {col.name}")
    print(f"    ID: {col.id}")
    print(f"    Vectors: {col.count()}")

print()
print(f"user_collection_* collections: {len(user_collections)}")
for col in user_collections:
    print(f"  - {col.name}")
    print(f"    ID: {col.id}")
    print(f"    Vectors: {col.count()}")

print()
print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()

# Extract user IDs from collection names
knowledge_chunks_user_ids = set()
for col in knowledge_chunks_collections:
    # Extract UUID from collection name: knowledge_chunks_<uuid>
    parts = col.name.split("_")
    if len(parts) >= 3:
        uuid_str = "_".join(parts[2:])  # Everything after "knowledge_chunks_"
        knowledge_chunks_user_ids.add(uuid_str)

user_collection_user_ids = set()
for col in user_collections:
    # Extract UUID from collection name: user_collection_<uuid>
    parts = col.name.split("_")
    if len(parts) >= 3:
        uuid_str = "_".join(parts[2:])  # Everything after "user_collection_"
        user_collection_user_ids.add(uuid_str)

print(f"Users with knowledge_chunks_* collections: {len(knowledge_chunks_user_ids)}")
for uid in knowledge_chunks_user_ids:
    print(f"  - {uid}")

print()
print(f"Users with user_collection_* collections: {len(user_collection_user_ids)}")
for uid in user_collection_user_ids:
    print(f"  - {uid}")

print()
print(f"Users with BOTH collection types: {len(knowledge_chunks_user_ids & user_collection_user_ids)}")
for uid in knowledge_chunks_user_ids & user_collection_user_ids:
    print(f"  - {uid}")

print()
print(f"Users with ONLY knowledge_chunks_*: {len(knowledge_chunks_user_ids - user_collection_user_ids)}")
for uid in knowledge_chunks_user_ids - user_collection_user_ids:
    print(f"  - {uid}")

print()
print(f"Users with ONLY user_collection_*: {len(user_collection_user_ids - knowledge_chunks_user_ids)}")
for uid in user_collection_user_ids - knowledge_chunks_user_ids:
    print(f"  - {uid}")
