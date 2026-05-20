from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from services.llama_service import stream_advice

router = APIRouter()

@router.get("/api/stream")
async def stream_sku_advice(sku: str, days: int = 14, stock: int = 150):
    # Seamlessly hands off query args to your background LLM stream
    return StreamingResponse(
        stream_advice(sku_id=sku, days=days, stock=stock), 
        media_type="text/event-stream"
    )