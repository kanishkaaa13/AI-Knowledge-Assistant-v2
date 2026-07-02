from app.db.session import db_manager
from app.models.user import User
from app.core.security import get_password_hash

db = db_manager.session_factory()
user = db.query(User).filter(User.email == 'kanishkaarde99@gmail.com').first()
if user:
    user.hashed_password = get_password_hash('test12345')
    db.commit()
    print('Password updated successfully')
else:
    print('User not found')
db.close()
