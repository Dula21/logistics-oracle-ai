import asyncio
from prophet import Prophet
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

async def run_forecast(sku_id: str, current_stock: int, history: list = None) -> dict:
    """
    Executes an unblocked event loop thread worker for Prophet computations,
    safely sourcing data from the historic telemetry CSV.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_forecast, sku_id, current_stock)

def _sync_forecast(sku_id: str, stock: int):
    # 1. Pull directly from your structured CSV engine
    try:
        df = pd.read_csv("historic_sales.csv")
    except FileNotFoundError:
        # Fallback structural mock to prevent initialization crashes
        return {"sku_id": sku_id, "days_until_stockout": 5, "forecast": [], "weekly_distribution": []}
    
    df_sku = df[df["SKU_ID"] == sku_id].copy()
    df_sku["Date"] = pd.to_datetime(df_sku["Date"])
    df_sku = df_sku.sort_values("Date")
    
    # Extract structural metrics for the Next.js visual cards
    recent_history = df_sku.tail(7)
    avg_sales = round(float(recent_history["Sales_Units"].mean()), 1)
    
    # Parse real weekly day names to construct your Weekly Run-Rate distribution
    df_sku["Day_Name"] = df_sku["Date"].dt.strftime("%a")
    weekly_map = df_sku.tail(14).groupby("Day_Name")["Sales_Units"].mean().round(0).to_dict()
    weekly_distribution = [{"day": k, "sales": int(v)} for k, v in weekly_map.items()]

    # 2. Build Prophet structural tracking fields
    df_input = df_sku[["Date", "Sales_Units", "Ramadan", "Promo_Active"]].rename(
        columns={"Date": "ds", "Sales_Units": "y"}
    )
    
    m = Prophet(weekly_seasonality=True, yearly_seasonality=True, daily_seasonality=False)
    m.add_regressor("Ramadan")
    m.add_regressor("Promo_Active")
    m.fit(df_input)
    
    # 3. Create Future Horizon Dates anchored to your target simulation frame
    future_start = datetime(2026, 2, 20)
    future_dates = [future_start + timedelta(days=x) for x in range(14)]
    future = pd.DataFrame({"ds": future_dates})
    
    # Map future timeline parameters dynamically so Prophet can project the spikes
    future["Ramadan"] = future["ds"].apply(
        lambda dt: 1 if ((dt.month == 2 and dt.day >= 18) or (dt.month == 3 and dt.day <= 19)) else 0
    )
    future["Promo_Active"] = future["ds"].apply(
        lambda dt: 1 if dt.day in [1, 28] else 0
    )
    
    forecast = m.predict(future)
    
    # 4. Accurate Stock Depletion Loop Processing
    points = []
    cumulative_stock = stock
    days_until_stockout = 14
    countdown = 0
    
    for _, row in forecast.iterrows():
        countdown += 1
        predicted_units = max(0.0, round(row["yhat"], 1))
        cumulative_stock -= predicted_units
        
        if cumulative_stock <= 0 and days_until_stockout == 14:
            days_until_stockout = countdown
            
        points.append({
            "date": row["ds"].strftime("%b %d"),
            "predicted_units": predicted_units,
            "lower_bound": max(0.0, round(row["yhat_lower"], 1)),
            "upper_bound": round(row["yhat_upper"], 1),
        })
        
    return {
        "sku_id": sku_id,
        "days_until_stockout": days_until_stockout,
        "avg_daily_sales": avg_sales,
        "forecast": points,
        "weekly_distribution": weekly_distribution
    }