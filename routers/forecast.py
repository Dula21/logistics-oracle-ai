from fastapi import APIRouter, Query
import pandas as pd
from data_engine import get_sku_data
from services.prophet_service import run_prophet_engine
from services.llama_service import get_llama_advice

router = APIRouter()

@router.get("/api/forecast")
async def get_forecast(sku: str = Query(default="A1023")):
    # 1. Fetch filtered structured records from CSV sheet
    sku_data = get_sku_data(sku)
    
    # 2. Run target Prophet calculation pass
    forecast_output = run_prophet_engine(sku_data["df_for_prophet"])
    
    # 3. Calculate stockout logic parameters
    stock = sku_data["current_stock"]
    running_total = 0
    days_until_stockout = 0
    rows_payload = []
    
    for _, row in forecast_output.iterrows():
        pred_val = max(0, int(round(row["yhat"])))
        running_total += pred_val
        if running_total <= stock:
            days_until_stockout += 1
            
        rows_payload.append({
            "date": row["ds"].strftime("%b %d"),
            "predicted": pred_val,
            "lower": max(0, int(row["yhat_lower"])),
            "upper": int(row["yhat_upper"])
        })
        
    # 4. Generate AI advisory insights
    ai_runbook = get_llama_advice(sku, stock, days_until_stockout)
    
    return {
        "sku_id": sku,
        "stock_on_hand": stock,
        "avg_sales": sku_data["avg_sales"],
        "days_to_stockout": days_until_stockout,
        "forecast_dates": [r["date"] for r in rows_payload],
        "forecast_rows": rows_payload,
        "advice": ai_runbook
    }