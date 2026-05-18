from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from services.llama_service import stream_advice
import pandas as pd

router = APIRouter(prefix="/stream", tags=["stream"])

@router.get("/")
async def stream_ai_insights(sku: str = Query(default="A1023")):
    """
    Exposes an active chunked transmission port to stream text to the UI.
    """
    # 1. Look up data frames to capture stock states
    try:
        df = pd.read_csv("historic_sales.csv")
        df_sku = df[df["SKU_ID"] == sku]
        stock_value = int(df_sku.iloc[-1]["Stock_On_Hand"]) if not df_sku.empty else 150
    except Exception:
        stock_value = 150
        
    # Mocking days remaining calculation for prompt optimization
    days_left = 5 if sku == "C9011" else 12

    # 2. Return an active text/event-stream response frame
    return StreamingResponse(
        stream_advice(sku_id=sku, days=days_left, stock=stock_value),
        media_type="text/event-stream"
    )