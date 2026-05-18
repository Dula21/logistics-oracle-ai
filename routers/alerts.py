from fastapi import APIRouter
from typing import List
from models.schemas import AlertStatus

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Global dictionary tracking stockout runways
_sku_forecasts: dict = {
    "A1023": 12,
    "B5842": 8,
    "C9011": 3
}

def register_forecast(sku_id: str, days_until_stockout: int):
    """
    Updates the shared storage dictionary with the calculated stockout timeline.
    """
    _sku_forecasts[sku_id] = days_until_stockout

@router.get("/", response_model=List[AlertStatus])
async def get_alerts():
    alerts = []
    for sku_id, days in list(_sku_forecasts.items()):
        if days <= 3:
            status = "red"
            message = f"🚨 CRITICAL: Stockout expected in {days} day(s). Emergency reorder required."
        elif days <= 7:
            status = "amber"
            message = f"⚠️ WARNING: Stock runway is {days} days. Prepare local logistics dispatch."
        else:
            status = "green"
            message = f"✅ STABLE: Inventory levels healthy ({days}+ days remaining)."
            
        alerts.append(AlertStatus(
            sku_id=sku_id,
            status=status,
            days_until_stockout=days,
            message=message,
        ))
    return alerts