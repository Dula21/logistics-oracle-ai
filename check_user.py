from database import engine, SessionLocal
from models.db_models import User

db = SessionLocal()
users = db.query(User).all()
print(f"Users in database: {len(users)}")
for u in users:
    print(f" - {u.email} | role: {u.role} | id: {u.id}")
db.close()