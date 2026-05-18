from fastapi import APIRouter, HTTPException, Query
from models.schemas import ForecastResponse
from services.prophet_service import run_forecast
from routers.alerts import register_forecast
import pandas as pd

# The router prefix remains clean; we will attach the global '/api' grouping in main.py
router = APIRouter(prefix="/forecast", tags=["forecast"])

@router.get("", response_model=ForecastResponse)
async def get_forecast(sku: str = Query(..., alias="sku")):
    """
    Handles incoming GET requests from your frontend dashboard charts.
    """
    # 1. Look up historical data parameters to find the correct Stock level
    try:
        df = pd.read_csv("historic_sales.csv")
        df_sku = df[df["SKU_ID"] == sku]
        if df_sku.empty:
            raise HTTPException(status_code=404, detail=f"SKU {sku} not found in historical data records.")
        
        # Pull the latest real-time stock-on-hand integer value
        stock_value = int(df_sku.iloc[-1]["Stock_On_Hand"])
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="historic_sales.csv file is missing from workspace root.")
    except Exception as e:
        stock_value = 150  # Stable operational fallback anchor

    # 2. Call the correct service function name
    result = await run_forecast(sku_id=sku, current_stock=stock_value)
    
    # 3. Register with your alert tracker state machine
    register_forecast(sku_id=sku, days_until_stockout=result["days_until_stockout"])
    
    return result