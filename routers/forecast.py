from fastapi import APIRouter

router = APIRouter()

@router.get("/api/forecast")
async def get_forecast(sku: str):
    # Match the exact snake_case fields used by the Next.js app/page.tsx file
    return {
        "sku_id": sku, 
        "avg_daily_sales": 12.5,
        "days_until_stockout": 14,
        "current_stock": 150,
        "weekly_distribution": [70, 85, 90, 65, 80, 95, 110],
        "forecast": [
            {"date": "Day 1", "units": 138},
            {"date": "Day 2", "units": 125},
            {"date": "Day 3", "units": 113},
            {"date": "Day 4", "units": 100},
            {"date": "Day 5", "units": 88},
            {"date": "Day 6", "units": 75},
            {"date": "Day 7", "units": 63}
        ]
    }