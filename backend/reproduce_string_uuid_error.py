"""
Reproduce the original error that occurred when user_id was passed as string.
This demonstrates the actual cause of the "0 rows" result.
"""

from app.db.session import get_db
from app.models.user import User

# Original error case: passing user_id as string instead of UUID
user_id_str = "12b2f540-96bf-4b44-92da-f263524a8662"

print("=" * 80)
print("TEST 1: Passing user_id as STRING (original error case)")
print("=" * 80)
print()

try:
    with next(get_db()) as db:
        user = db.query(User).filter(User.id == user_id_str).first()
        if user:
            print(f"User found: {user.email}")
        else:
            print("User NOT found in database")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print()
print("=" * 80)
print("TEST 2: Passing user_id as UUID (correct case)")
print("=" * 80)
print()

import uuid
user_id_uuid = uuid.UUID(user_id_str)

try:
    with next(get_db()) as db:
        user = db.query(User).filter(User.id == user_id_uuid).first()
        if user:
            print(f"User found: {user.email}")
            print(f"ID: {user.id}")
        else:
            print("User NOT found in database")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
