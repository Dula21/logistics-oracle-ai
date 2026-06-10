from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-dev-only")
ALGORITHM = "HS256"

payload = {
    "sub": "admin_user",
    "role": "admin",
    "exp": datetime.utcnow() + timedelta(days=30)
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(f"\nYour JWT token:\n\n{token}\n")
print("Save this — paste it into your frontend .env as NEXT_PUBLIC_ADMIN_TOKEN")