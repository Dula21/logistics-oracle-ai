import asyncio
import json
import os

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services.llama_service import stream_advice

router = APIRouter()

MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3.2")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/api/generate")

_insights_cache: dict[str, str] = {}


# =====================================================================
# ENDPOINT 1: Operational dashboard advice
# =====================================================================
@router.get("/api/stream")
async def stream_sku_advice(sku: str, days: int = 14, stock: int = 150):
    return StreamingResponse(
        stream_advice(sku_id=sku, days=days, stock=stock),
        media_type="text/plain"
    )


# =====================================================================
# ENDPOINT 2: Strategic 2026 planning advice
# =====================================================================
async def _stream_insights_advice(
    sku_id: str,
    ramadan_factor: float,
    promo_factor: float,
    avg_daily_sales: float,
    data_points: int
):
    cache_key = f"insights_{sku_id}_{ramadan_factor}_{promo_factor}"

    if cache_key in _insights_cache:
        cached = _insights_cache[cache_key]
        for word in cached.split(" "):
            yield word + " "
            await asyncio.sleep(0.01)
        return

    # GUARDRAIL INTEGRATION: Wrapped explicit 2026 timeline and domain rules inside the system prompt
    prompt_message = (
        f"System Role: Dubai logistics and regional supply chain consultant. "
        f"Context Input: SKU {sku_id}: {avg_daily_sales} units/day, Ramadan scaling {ramadan_factor}x, promo scaling {promo_factor}x. "
        f"Strategic Guardrails:\n"
        f"- Provide exactly 2 sentences regarding Ramadan 2026 reorder timing and buffer quantity metrics.\n"
        f"- Do not use markdown syntax, bolding, or header tokens.\n"
        f"- Restrict domain scope exclusively to warehouse buffer capacities and logistics timelines."
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_message,
        "stream": True,
        "options": {"num_predict": 80}
    }
    full_text = ""
    timeout_config = httpx.Timeout(120.0, connect=5.0, read=120.0)

    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                if response.status_code != 200:
                    yield f"◈ [Engine Error] HTTP {response.status_code}"
                    return

                # LIST OF RESTRICTED TOPICS FOR TRANSIT DATA CLEANLINESS
                PROHIBITED_TOPICS = ["crypto", "bitcoin", "pricing", "stocks", "shares", "marketing", "hiring"]

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        json_data = json.loads(line)
                        token = json_data.get("response", "")
                        if token:
                            full_text += token
                            
                            # ACTIVE MID-STREAM INSPECTOR:
                            # Terminate immediately if token generation strays outside bounds
                            if any(topic in full_text.lower() for topic in PROHIBITED_TOPICS):
                                yield "\n⚠️ [Stream Terminated]: Content flagged by domain boundary guardrail."
                                return
                                
                            yield token
                    except json.JSONDecodeError:
                        continue

        if full_text.strip():
            _insights_cache[cache_key] = full_text

    except httpx.ConnectError:
        yield f"◈ [Connection Error] Ollama unreachable at {OLLAMA_URL}."
    except httpx.ReadTimeout:
        yield "⚠️ [Timeout] LLM took too long to respond."


@router.get("/api/stream/insights")
async def stream_insights_advice(
    sku: str,
    ramadan_factor: float = 1.8,
    promo_factor: float = 1.3,
    avg_daily_sales: float = 0.0,
    data_points: int = 0
):
    return StreamingResponse(
        _stream_insights_advice(
            sku_id=sku,
            ramadan_factor=ramadan_factor,
            promo_factor=promo_factor,
            avg_daily_sales=avg_daily_sales,
            data_points=data_points
        ),
        media_type="text/plain"
    )