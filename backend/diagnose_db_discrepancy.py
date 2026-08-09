"""
Diagnose SQL query discrepancy for user 12b2f540.
Check exact database file path and verify which database is being used.
"""

import os
from pathlib import Path

print("=" * 80)
print("DATABASE FILE PATH INVESTIGATION")
print("=" * 80)
print()

# Check current working directory
cwd = os.getcwd()
print(f"Current working directory: {cwd}")
print()

# Check app.core.config settings
from app.core.config import settings
print(f"settings.DATABASE_URL: {settings.DATABASE_URL}")
print()

# Check if DATABASE_URL is SQLite and extract path
if settings.DATABASE_URL.startswith("sqlite:///"):
    db_path_from_config = settings.DATABASE_URL.replace("sqlite:///", "")
    print(f"Database path from config: {db_path_from_config}")
    abs_db_path = os.path.abspath(db_path_from_config)
    print(f"Absolute database path: {abs_db_path}")
    print(f"Database file exists: {os.path.exists(abs_db_path)}")
    print()
else:
    print("DATABASE_URL is not SQLite")
    print()

# Check for ai_knowledge_assistant.db in current directory
local_db = Path("ai_knowledge_assistant.db")
print(f"Local ai_knowledge_assistant.db exists: {local_db.exists()}")
if local_db.exists():
    print(f"Absolute path: {local_db.resolve()}")
    print(f"File size: {local_db.stat().st_size} bytes")
print()

# Check backend directory
backend_dir = Path("backend")
backend_db = backend_dir / "ai_knowledge_assistant.db"
print(f"Backend/ai_knowledge_assistant.db exists: {backend_db.exists()}")
if backend_db.exists():
    print(f"Absolute path: {backend_db.resolve()}")
    print(f"File size: {backend_db.stat().st_size} bytes")
print()

# Now query the actual database being used
print("=" * 80)
print("QUERYING ACTUAL DATABASE")
print("=" * 80)
print()

from app.db.session import get_db
from app.models.user import User
import uuid

user_id = uuid.UUID("12b2f540-96bf-4b44-92da-f263524a8662")

with next(get_db()) as db:
    # Get the actual engine URL
    print(f"Database engine URL: {db.bind.url}")
    print()
    
    # Query user
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        print(f"User FOUND in database:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.name}")
    else:
        print("User NOT found in database")
    
    print()
    
    # Count all users
    total_users = db.query(User).count()
    print(f"Total users in database: {total_users}")
    
    # List all users
    all_users = db.query(User).all()
    print("All users:")
    for u in all_users:
        print(f"  - {u.id}: {u.email}")
