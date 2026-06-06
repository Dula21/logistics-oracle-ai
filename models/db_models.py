from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean
from database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="manager")
    created_at = Column(DateTime, default=datetime.utcnow)

class ReorderDecision(Base):
    __tablename__ = "reorder_decisions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)
    sku_id = Column(String, nullable=False)
    stock = Column(Integer, nullable=True)
    days_until_stockout = Column(Integer, nullable=True)
    avg_daily_sales = Column(Float, nullable=True)
    advice = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)