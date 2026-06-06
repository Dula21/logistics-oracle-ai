from database import SessionLocal
from models.db_models import User
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

# Check if admin already exists
existing = db.query(User).filter(User.email == "superadmin@oracle.ae").first()
if existing:
    print("Admin already exists")
else:
    admin = User(
        id=str(uuid.uuid4()),
        email="superadmin@oracle.ae",
        hashed_password=pwd_context.hash("OracleAdmin2026!"),
        role="admin"
    )
    db.add(admin)
    db.commit()
    print(f"Admin created: {admin.email} | role: {admin.role}")

db.close()