import asyncio
import json
import os

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services.llama_service import stream_advice

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3-8b-8192")

_insights_cache: dict[str, str] = {}

PROHIBITED_TOPICS = ["crypto", "bitcoin", "stocks", "shares", "marketing", "hiring"]


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

    if not GROQ_API_KEY:
        yield "⚠️ GROQ_API_KEY not set in environment."
        return

    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior supply chain consultant for Dubai SMEs in JAFZA and D3. "
                "Provide logistics advice only — warehouse buffers and procurement timelines. "
                "Never use markdown, bullets, or headers."
            )
        },
        {
            "role": "user",
            "content": (
                f"SKU {sku_id}: {avg_daily_sales} units/day average sales. "
                f"Ramadan demand spikes {ramadan_factor}x, promo events spike {promo_factor}x. "
                f"Give exactly 2 sentences: when to reorder for Ramadan 2026 and how much buffer stock to hold."
            )
        }
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "max_tokens": 120,
        "temperature": 0.3,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    full_text = ""
    timeout_config = httpx.Timeout(30.0, connect=5.0, read=30.0)

    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            async with client.stream("POST", GROQ_URL, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error = await response.aread()
                    yield f"◈ [Groq Error] HTTP {response.status_code}: {error.decode()[:200]}"
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        token = chunk["choices"][0]["delta"].get("content", "")
                        if token:
                            full_text += token

                            # Domain guardrail
                            if any(t in full_text.lower() for t in PROHIBITED_TOPICS):
                                yield "\n⚠️ [Guardrail]: Content outside logistics domain detected."
                                return

                            yield token
                    except (json.JSONDecodeError, KeyError):
                        continue

        if full_text.strip():
            _insights_cache[cache_key] = full_text

    except httpx.ConnectError:
        yield "◈ [Connection Error] Cannot reach Groq API. Check your network."
    except httpx.ReadTimeout:
        yield "⚠️ [Timeout] Groq took too long to respond."


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