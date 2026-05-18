from pydantic import BaseModel, Field
from typing import List, Optional

class ForecastPoint(BaseModel):
    date: str = Field(..., description="Formatted string date (e.g. Feb 22)")
    predicted_units: float
    lower_bound: float
    upper_bound: float

class WeeklyDistributionItem(BaseModel):
    day: str = Field(..., description="Three-letter day name shortcut (e.g. Fri)")
    sales: int

class ForecastRequest(BaseModel):
    sku_id: str
    stock_on_hand: Optional[int] = None

class ForecastResponse(BaseModel):
    sku_id: str
    days_until_stockout: int
    avg_daily_sales: float
    forecast: List[ForecastPoint]
    weekly_distribution: List[WeeklyDistributionItem]

class AlertStatus(BaseModel):
    sku_id: str
    status: str = Field(..., description="Traffic light categorization: red, amber, green")
    days_until_stockout: int
    message: str