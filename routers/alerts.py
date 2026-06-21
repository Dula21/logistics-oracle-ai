from fastapi import APIRouter, HTTPException
import asyncio
import pandas as pd

from routers.upload import get_active_csv
from services.prophet_service import run_forecast
from logger import get_logger

logger = get_logger("alerts")
router = APIRouter(tags=["Alerts"])


@router.get("/api/alerts")
async def get_alerts():
    logger.info("alerts_request")

    try:
        csv_path = get_active_csv()
        df = pd.read_csv(csv_path)
        df.columns = [col.strip() for col in df.columns]
        skus = df["SKU_ID"].astype(str).str.strip().str.upper().unique().tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV read error: {str(e)}")

    if not skus:
        return {"alerts": []}

    results = await asyncio.gather(
        *[run_forecast(sku_id=sku, current_stock=0, mode="operational") for sku in skus],
        return_exceptions=True
    )

    alerts = []
    for sku, result in zip(skus, results):
        if isinstance(result, Exception):
            continue

        days = result["days_until_stockout"]
        stock = result["current_stock"]
        avg_sales = result["avg_daily_sales"]

        if days <= 7:
            status = "red"
            message = f"CRITICAL: Stockout in {days} days. Emergency reorder required."
        elif days <= 14:
            status = "amber"
            message = f"WARNING: {days} days runway. Prepare reorder now."
        else:
            status = "green"
            message = f"STABLE: {days} days of stock remaining."

        alerts.append({
            "sku_id": sku,
            "status": status,
            "days_until_stockout": days,
            "current_stock": stock,
            "avg_daily_sales": avg_sales,
            "message": message,
        })

    priority = {"red": 0, "amber": 1, "green": 2}
    alerts.sort(key=lambda x: (priority[x["status"]], x["days_until_stockout"]))

    logger.info("alerts_success", total=len(alerts), red=sum(1 for a in alerts if a["status"] == "red"))

    return {"alerts": alerts}