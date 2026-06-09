import os
import sys
import json
import httpx
import asyncio
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv 
from pydantic import BaseModel
from typing import List


load_dotenv()
router = APIRouter()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.prophet_service import run_forecast

MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama-3.1-8b-instant")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/api/generate")

_advice_cache: dict[str, str] = {}


# =====================================================================
# ENDPOINT 1: Operational Dashboard (last 60 days)
# =====================================================================
@router.get("/api/forecast")
async def get_forecast(sku: str = Query(..., description="Target SKU identification string")):
    """
    Returns operational data scoped to last 60 days for dashboard KPIs and depletion chart.
    """
    try:
        analytics_payload = await run_forecast(sku_id=sku, current_stock=0, mode="operational")
        return analytics_payload
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Operational forecast error: {str(err)}"
        )


# =====================================================================
# ENDPOINT 2: Strategic Insights (full 2024 + 2025 history)
# =====================================================================
@router.get("/api/insights")
async def get_insights(sku: str = Query(..., description="Target SKU identification string")):
    """
    Returns full 2024-2025 historical data for the seasonal insights comparison page.
    Includes all Ramadan and promo spike annotations across both years.
    """
    try:
        analytics_payload = await run_forecast(sku_id=sku, current_stock=0, mode="strategic")
        return analytics_payload
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Strategic insights error: {str(err)}"
        )


# =====================================================================
# ENDPOINT 3: Token Streaming Logic Gateway
# =====================================================================
async def generate_stream_tokens(sku_id: str, days: int, stock: int, ramadan_factor: float, promo_factor: float):
    cache_key = f"{sku_id}_{days}_{stock}"

    if cache_key in _advice_cache:
        cached_text = _advice_cache[cache_key]
        words = cached_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.01)
        return

    prompt_message = (
        f"You are an expert logistics consultant for Dubai SMEs in D3/JAFZA. "
        f"Analyze these inventory metrics for SKU {sku_id}: "
        f"Remaining Stock: {stock} units. Runway Left: exactly {days} days before total stockout. "
        f"Historical Ramadan sales spike multiplier: {ramadan_factor}x. "
        f"Historical Promo weekend sales multiplier: {promo_factor}x. "
        f"Write a single concise paragraph of operational advice (max 3 sentences). "
        f"Tell the owner exactly when to reorder and how much, factoring in these seasonal spikes. "
        f"Keep it professional and human. Do not use markdown headers, bolding, asterisks, or list formats."
    )

    payload = {"model": MODEL_NAME, "prompt": prompt_message, "stream": True}
    full_generated_text = ""
    timeout_config = httpx.Timeout(60.0, connect=5.0, read=60.0)

    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                if response.status_code != 200:
                    yield f"◈ [Engine Error] HTTP Status Code: {response.status_code}"
                    return

                async for chunk in response.aiter_text():
                    if not chunk.strip():
                        continue
                    for line in chunk.split("\n"):
                        if line.strip():
                            try:
                                json_data = json.loads(line)
                                token = json_data.get("response", "")
                                if token:
                                    full_generated_text += token
                                    yield token
                            except json.JSONDecodeError:
                                continue

        if full_generated_text.strip():
            _advice_cache[cache_key] = full_generated_text

    except httpx.ConnectError:
        yield f"◈ [Connection Breakpoint] Ollama unreachable at {OLLAMA_URL}."
    except httpx.ReadTimeout:
        yield "⚠️ [Processing Timeout] LLM engine took too long to respond."
        
        

class BatchForecastRequest(BaseModel):
    skus: List[str]
    mode: str = "operational"

@router.post("/api/forecast/batch")
async def forecast_batch(request: BatchForecastRequest):
    """
    Returns forecasts for multiple SKUs in parallel.
    Max 20 SKUs per request.
    """
    if len(request.skus) == 0:
        raise HTTPException(status_code=400, detail="No SKUs provided")
    
    if len(request.skus) > 20:
        raise HTTPException(status_code=400, detail="Max 20 SKUs per request")

    results = await asyncio.gather(
        *[run_forecast(sku_id=sku, current_stock=0, mode=request.mode) 
          for sku in request.skus],
        return_exceptions=True
    )

    forecasts = []
    errors = []
    for sku, result in zip(request.skus, results):
        if isinstance(result, Exception):
            errors.append({"sku": sku, "error": str(result)})
        else:
            forecasts.append(result)

    return {"forecasts": forecasts, "errors": errors}