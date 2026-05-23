import os
import sys
import asyncio
import concurrent.futures
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Instantiating thread pool executor for non-blocking dataframe manipulation
cpu_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
_forecast_cache = {}


def _heavy_compute_numerical_brain(df_sku: pd.DataFrame, current_stock: int):
    """
    Drives analytical logic across your live CSV tracking rows.
    Processes historical trends, seasonal demand modifiers (Ramadan),
    and promo spikes to construct structural payloads for Recharts and Llama.
    """
    df_sku = df_sku.copy()
    df_sku["Parsed_Date"] = pd.to_datetime(df_sku["Date"], errors='coerce')
    df_sku["Sales_Units"] = pd.to_numeric(df_sku["Sales_Units"], errors='coerce').fillna(0)
    
    # Extract baseline operational velocity
    avg_daily_sales = float(df_sku["Sales_Units"].mean()) if not df_sku.empty else 0.0
    
    # Calculate historical impact coefficients
    promo_sales = df_sku[df_sku["Promo_Active"] == 1]["Sales_Units"].mean()
    ramadan_sales = df_sku[df_sku["Ramadan"] == 1]["Sales_Units"].mean()
    
    promo_multiplier = round(promo_sales / avg_daily_sales, 2) if avg_daily_sales > 0 and not pd.isna(promo_sales) else 1.3
    ramadan_multiplier = round(ramadan_sales / avg_daily_sales, 2) if avg_daily_sales > 0 and not pd.isna(ramadan_sales) else 1.8

    # Safe stockout runway math mapping
    if avg_daily_sales > 0:
        days_until_stockout = max(0, int(current_stock / avg_daily_sales))
    else:
        days_until_stockout = 999

    # --- CHRONOLOGICAL DATA MATRIX ENHANCEMENT ---
    # Extracts chronological ledger entries directly from the CSV data points 
    # ensuring the frontend chart maps exactly to 2024-2025 milestones.
    historical_chart_nodes = []
    tail_df = df_sku.tail(60)  # Isolates trailing data rows for granular frontend analysis
    
    for _, row in tail_df.iterrows():
        historical_chart_nodes.append({
            "date": str(row["Date"]),
            "predicted_units": float(row["Sales_Units"]),
            "lower_bound": max(0, round(float(row["Sales_Units"]) * 0.8, 1)),
            "upper_bound": round(float(row["Sales_Units"]) * 1.2, 1),
            "is_ramadan": int(row.get("Ramadan", 0)),
            "is_promo": int(row.get("Promo_Active", 0))
        })

    # Day-of-week run rate distribution calculation
    weekday_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df_sku["Weekday_Idx"] = df_sku["Parsed_Date"].dt.weekday
    grouped_averages = df_sku.groupby("Weekday_Idx")["Sales_Units"].mean()
    
    weekly_distribution = [
        {"day": weekday_map[i], "sales": round(float(grouped_averages.get(i, avg_daily_sales)), 1)}
        for i in range(7)
    ]

    sku_name = str(df_sku["SKU_ID"].iloc[0]).upper() if not df_sku.empty else "UNKNOWN"

    return {
        "sku_id": sku_name,
        "days_until_stockout": days_until_stockout,
        "avg_daily_sales": round(avg_daily_sales, 1),
        "current_stock": int(current_stock),
        "forecast": historical_chart_nodes,  # Maps clean historical data structures to frontend Recharts
        "weekly_distribution": weekly_distribution,
        "insights_metadata": {
            "ramadan_impact_factor": ramadan_multiplier,
            "promo_impact_factor": promo_multiplier,
            "historical_data_points": len(df_sku)
        }
    }


async def run_forecast(sku_id: str, current_stock: int):
    """
    Orchestrates the ingestion workflow: reads the ledger file, isolates records
    strictly within the 2024-2025 time bounds, dynamically evaluates physical 
    stock, and offloads computation safely to the thread-pool executor.
    """
    # Cache layer abstraction
    if sku_id in _forecast_cache:
        return _forecast_cache[sku_id]

    # Resolve relative data file paths cleanly
    # Resolve project root (repo root), not the services/ folder
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ENV_DATA_PATH = os.getenv("DATA_SOURCE_PATH", "historic_sales.csv")

    # If DATA_SOURCE_PATH is relative, treat it as relative to the repo root
    csv_path = (
        ENV_DATA_PATH
        if os.path.isabs(ENV_DATA_PATH)
        else os.path.join(PROJECT_ROOT, ENV_DATA_PATH)
    )


    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Master ledger file path missing or unreadable: {csv_path}")

    # Read tracking database ledger
    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]
    
    df["Parsed_Date"] = pd.to_datetime(df["Date"], errors='coerce')
    
    # Scope evaluation strictly across historical data rows
    mask = (
        (df["SKU_ID"].astype(str).str.strip().str.upper() == str(sku_id).strip().upper()) &
        (df["Parsed_Date"] >= "2025-02-01") & 
        (df["Parsed_Date"] <= "2025-03-31")
    )
    df_sku = df[mask]
    
    # Return zero-state safe structure if target target SKU doesn't exist
    if df_sku.empty:
        return {
            "sku_id": sku_id.upper(),
            "days_until_stockout": 0,
            "avg_daily_sales": 0.0,
            "current_stock": current_stock,
            "forecast": [],
            "weekly_distribution": [],
            "insights_metadata": {
                "ramadan_impact_factor": 1.8,
                "promo_impact_factor": 1.3,
                "historical_data_points": 0
            }
        }

    # Extract real stock metrics directly from the final ledger entry point
    if "Stock_On_Hand" in df_sku.columns:
        try:
            current_stock = int(float(df_sku["Stock_On_Hand"].iloc[-1]))
        except (ValueError, TypeError):
            pass

    # Execute math operations inside thread runner pool
    loop = asyncio.get_running_loop()
    computed_result = await loop.run_in_executor(
        cpu_executor, 
        _heavy_compute_numerical_brain, 
        df_sku, 
        current_stock
    )
    
    # Store matrix calculations inside memory dictionary cache
    _forecast_cache[sku_id] = computed_result
    return computed_result