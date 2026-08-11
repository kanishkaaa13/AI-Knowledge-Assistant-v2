"""
Find the email for user 2f9c2a2c.
"""

import uuid
from app.db.session import get_db
from app.models.user import User

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

with next(get_db()) as db:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
    else:
        print("User not found")
