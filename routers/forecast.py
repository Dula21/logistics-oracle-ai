import os
import sys
import json
import httpx
import asyncio
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# --- RUNTIME PATH CONFIGURATION ---
# Appends parent project root directory so that prophet_service can be found cleanly
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.prophet_service import run_forecast

# Global configuration variables
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3.2")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/api/generate")

# Memory caches to keep things fast
_advice_cache: dict[str, str] = {}


# =====================================================================
# ENDPOINT 1: Static Numerical Matrix Engine (Matches Next.js Step 1)
# =====================================================================
@router.get("/api/forecast")
async def get_forecast(sku: str = Query(..., description="Target SKU identification string")):
    """
    Returns the core mathematical dataset parsed strictly from 2024/2025 rows.
    """
    try:
        analytics_payload = await run_forecast(sku_id=sku, current_stock=0)
        return analytics_payload
    except Exception as err:
        raise HTTPException(
            status_code=500, 
            detail=f"Logistics Framework Numerical Parsing error: {str(err)}"
        )


# =====================================================================
# ENDPOINT 2: Token Streaming Logic Gateway (Matches Next.js Step 2)
# =====================================================================
async def generate_stream_tokens(sku_id: str, days: int, stock: int, ramadan_factor: float, promo_factor: float):
    cache_key = f"{sku_id}_{days}_{stock}"

    # 1. Cache hit abstraction layer: stream out instantly if computed before
    if cache_key in _advice_cache:
        cached_text = _advice_cache[cache_key]
        words = cached_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.01)
        return

    # Rich contextual business intelligence prompt customized for Dubai SMEs
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

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_message,
        "stream": True,
    }

    full_generated_text = ""
    timeout_config = httpx.Timeout(60.0, connect=5.0, read=60.0)

    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                if response.status_code != 200:
                    yield f"◈ [Engine Error] HTTP Status Code: {response.status_code}"
                    return

                # Read chunk blocks directly down the line
                async for chunk in response.aiter_text():
                    if not chunk.strip():
                        continue

                    lines = chunk.split("\n")
                    for line in lines:
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
        yield (
            f"◈ [Connection Breakpoint]\n"
            f"Ollama is unreachable at {OLLAMA_URL}. Ensure your local terminal "
            f"is running 'ollama run {MODEL_NAME}'."
        )
    except httpx.ReadTimeout:
        yield (
            f"⚠️ [Processing Timeout]\n"
            f"The local LLM engine took too long to generate an advisory token sequence."
        )


# NOTE:
# /api/stream is intentionally implemented in routers/stream.py using services/llama_service.py.
# This avoids conflicting duplicate route implementations.

