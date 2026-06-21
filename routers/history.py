from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from database import get_db
from models.db_models import ReorderDecision
from auth.dependencies import verify_token

router = APIRouter(tags=["History"])


class DecisionInput(BaseModel):
    sku_id: str
    stock: int
    days_until_stockout: int
    avg_daily_sales: float
    advice: str
    status: str


@router.post("/api/history/save")
def save_decision(
    body: DecisionInput,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    entry = ReorderDecision(
        id=str(uuid.uuid4()),
        user_id=user_id,
        sku_id=body.sku_id,
        stock=body.stock,
        days_until_stockout=body.days_until_stockout,
        avg_daily_sales=body.avg_daily_sales,
        advice=body.advice,
        status=body.status,
        created_at=datetime.utcnow()
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "created_at": entry.created_at.isoformat()}


@router.get("/api/history")
def get_history(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    entries = (
        db.query(ReorderDecision)
        .filter(ReorderDecision.user_id == user_id)
        .order_by(ReorderDecision.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "entries": [
            {
                "id": e.id,
                "timestamp": e.created_at.isoformat(),
                "sku_id": e.sku_id,
                "stock": e.stock,
                "days_until_stockout": e.days_until_stockout,
                "avg_daily_sales": e.avg_daily_sales,
                "advice": e.advice,
                "status": e.status,
            }
            for e in entries
        ]
    }


@router.delete("/api/history/{entry_id}")
def delete_decision(
    entry_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    entry = db.query(ReorderDecision).filter(
        ReorderDecision.id == entry_id,
        ReorderDecision.user_id == user_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"deleted": entry_id}


@router.delete("/api/history")
def clear_history(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db.query(ReorderDecision).filter(
        ReorderDecision.user_id == user_id
    ).delete()
    db.commit()
    return {"cleared": True}