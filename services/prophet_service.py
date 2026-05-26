import os
import asyncio
import concurrent.futures
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

cpu_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
_forecast_cache = {}


def _project_2026(df_sku: pd.DataFrame, avg_daily_sales: float, ramadan_multiplier: float, promo_multiplier: float):
    """
    Projects Feb + Mar 2026 from 2025 same-period patterns.
    Applies Ramadan and promo multipliers to matching day-of-year rows.
    """
    # Pull Feb + Mar 2025 as the base pattern
    df_sku["Parsed_Date"] = pd.to_datetime(df_sku["Date"], errors="coerce")
    base = df_sku[
        (df_sku["Parsed_Date"] >= "2025-02-01") &
        (df_sku["Parsed_Date"] <= "2025-03-31")
    ].copy()

    projected = []
    for _, row in base.iterrows():
        original_date = row["Parsed_Date"]
        # Shift date forward exactly 1 year
        projected_date = original_date.replace(year=2026)

        is_ramadan = int(row.get("Ramadan", 0))
        is_promo = int(row.get("Promo_Active", 0))

        # Apply multipliers to base sales
        base_units = float(row["Sales_Units"])
        if is_ramadan:
            units = round(base_units * ramadan_multiplier, 1)
        elif is_promo:
            units = round(base_units * promo_multiplier, 1)
        else:
            units = round(base_units, 1)

        projected.append({
            "date": projected_date.strftime("%Y-%m-%d"),
            "predicted_units": units,
            "lower_bound": max(0, round(units * 0.8, 1)),
            "upper_bound": round(units * 1.2, 1),
            "is_ramadan": is_ramadan,
            "is_promo": is_promo
        })

    return projected


def _heavy_compute_numerical_brain(df_sku: pd.DataFrame, current_stock: int, mode: str = "operational"):
    """
    mode="operational" → projects Feb+Mar 2026 from 2025 patterns (dashboard)
    mode="strategic"   → full 2024+2025 actuals (insights page)
    """
    df_sku = df_sku.copy()
    df_sku["Parsed_Date"] = pd.to_datetime(df_sku["Date"], errors="coerce")
    df_sku["Sales_Units"] = pd.to_numeric(df_sku["Sales_Units"], errors="coerce").fillna(0)
    df_sku = df_sku.sort_values("Parsed_Date")

    avg_daily_sales = float(df_sku["Sales_Units"].mean()) if not df_sku.empty else 0.0

    promo_sales = df_sku[df_sku["Promo_Active"] == 1]["Sales_Units"].mean()
    ramadan_sales = df_sku[df_sku["Ramadan"] == 1]["Sales_Units"].mean()

    promo_multiplier = round(promo_sales / avg_daily_sales, 2) if avg_daily_sales > 0 and not pd.isna(promo_sales) else 1.3
    ramadan_multiplier = round(ramadan_sales / avg_daily_sales, 2) if avg_daily_sales > 0 and not pd.isna(ramadan_sales) else 1.8

    days_until_stockout = max(0, int(current_stock / avg_daily_sales)) if avg_daily_sales > 0 else 999

    # Day-of-week distribution (always from full dataset)
    weekday_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df_sku["Weekday_Idx"] = df_sku["Parsed_Date"].dt.weekday
    grouped_averages = df_sku.groupby("Weekday_Idx")["Sales_Units"].mean()
    weekly_distribution = [
        {"day": weekday_map[i], "sales": round(float(grouped_averages.get(i, avg_daily_sales)), 1)}
        for i in range(7)
    ]

    sku_name = str(df_sku["SKU_ID"].iloc[0]).upper() if not df_sku.empty else "UNKNOWN"

    if mode == "operational":
        # Project Feb + Mar 2026 from 2025 patterns
        chart_nodes = _project_2026(df_sku, avg_daily_sales, ramadan_multiplier, promo_multiplier)
    else:
        # Strategic: return full 2024+2025 actuals
        chart_nodes = []
        for _, row in df_sku.iterrows():
            chart_nodes.append({
                "date": str(row["Date"]),
                "predicted_units": float(row["Sales_Units"]),
                "lower_bound": max(0, round(float(row["Sales_Units"]) * 0.8, 1)),
                "upper_bound": round(float(row["Sales_Units"]) * 1.2, 1),
                "is_ramadan": int(row.get("Ramadan", 0)),
                "is_promo": int(row.get("Promo_Active", 0))
            })

    return {
        "sku_id": sku_name,
        "days_until_stockout": days_until_stockout,
        "avg_daily_sales": round(avg_daily_sales, 1),
        "current_stock": int(current_stock),
        "forecast": chart_nodes,
        "weekly_distribution": weekly_distribution,
        "insights_metadata": {
            "ramadan_impact_factor": ramadan_multiplier,
            "promo_impact_factor": promo_multiplier,
            "historical_data_points": len(df_sku),
            "mode": mode
        }
    }


async def run_forecast(sku_id: str, current_stock: int, mode: str = "operational"):
    cache_key = f"{sku_id}_{mode}"
    if cache_key in _forecast_cache:
        return _forecast_cache[cache_key]

    # Use dynamically active CSV (switches on upload, resets on reset)
    try:
        from routers.upload import get_active_csv
        csv_path = get_active_csv()
    except ImportError:
        PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        ENV_DATA_PATH = os.getenv("DATA_SOURCE_PATH", "historic_sales.csv")
        csv_path = (
            ENV_DATA_PATH
            if os.path.isabs(ENV_DATA_PATH)
            else os.path.join(PROJECT_ROOT, ENV_DATA_PATH)
        )

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Master ledger file missing: {csv_path}")

    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]
    df["Parsed_Date"] = pd.to_datetime(df["Date"], errors="coerce")

    sku_filter = df["SKU_ID"].astype(str).str.strip().str.upper() == str(sku_id).strip().upper()

    if mode == "operational":
        # Load full history so multipliers are calculated accurately
        mask = (
            sku_filter &
            (df["Parsed_Date"] >= "2024-01-01") &
            (df["Parsed_Date"] <= "2025-12-31")
        )
    else:
        # Strategic: full 2024+2025
        mask = (
            sku_filter &
            (df["Parsed_Date"] >= "2024-01-01") &
            (df["Parsed_Date"] <= "2025-12-31")
        )

    df_sku = df[mask]

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
                "historical_data_points": 0,
                "mode": mode
            }
        }

    if "Stock_On_Hand" in df_sku.columns:
        try:
            current_stock = int(float(df_sku["Stock_On_Hand"].iloc[-1]))
        except (ValueError, TypeError):
            pass

    loop = asyncio.get_running_loop()
    computed_result = await loop.run_in_executor(
        cpu_executor,
        _heavy_compute_numerical_brain,
        df_sku,
        current_stock,
        mode
    )

    _forecast_cache[cache_key] = computed_result
    return computed_result