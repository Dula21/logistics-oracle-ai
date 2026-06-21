from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid
import os

from database import get_db
from models.db_models import User

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-dev-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register")
def register(
    form: OAuth2PasswordRequestForm = Depends(),
    role: str = Form("manager"),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == form.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate role
    allowed_roles = ["manager", "warehouse", "finance"]
    if role not in allowed_roles:
        role = "manager"

    user = User(
        id=str(uuid.uuid4()),
        email=form.username,
        hashed_password=pwd_context.hash(form.password),
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not pwd_context.verify(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.get("/me")
def get_me(db: Session = Depends(get_db), token: str = Depends(lambda: None)):
    return {"message": "Auth working"}


