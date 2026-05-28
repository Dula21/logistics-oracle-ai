import os
import httpx
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3-8b-8192")

_advice_cache = {}


async def stream_advice(sku_id: str, days: int, stock: int):
    cache_key = f"{sku_id}_{days}_{stock}"

    # Cache hit — replay instantly
    if cache_key in _advice_cache:
        cached_text = _advice_cache[cache_key]
        for i, word in enumerate(cached_text.split(" ")):
            yield word + (" " if i < len(cached_text.split(" ")) - 1 else "")
            await asyncio.sleep(0.01)
        return

    if not GROQ_API_KEY:
        yield "⚠️ GROQ_API_KEY not set in environment."
        return

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert logistics analyzer for Dubai SMEs operating in JAFZA and D3. "
                "Give sharp, actionable inventory advice. "
                "Never use markdown, headers, or bullet points. "
                "If days to stockout is under 7, prioritize immediate reorder urgently."
            )
        },
        {
            "role": "user",
            "content": (
                f"SKU {sku_id} has {stock} units left and will stock out in {days} days. "
                f"Give a 2-sentence action recommendation for the logistics team."
            )
        }
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "max_tokens": 120,
        "temperature": 0.4,
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
                            yield token
                    except (json.JSONDecodeError, KeyError):
                        continue

        # Critical days guardrail
        if days < 7 and full_text:
            text_upper = full_text.upper()
            if any(w in text_upper for w in ["WAIT", "MONITOR", "DELAY", "STABLE", "SECURE"]):
                override = "\n⚠️ [Guardrail]: Runway CRITICAL — initiate immediate procurement."
                yield override
                full_text += override

        if full_text.strip():
            _advice_cache[cache_key] = full_text

    except httpx.ConnectError:
        yield "◈ [Connection Error] Cannot reach Groq API. Check your network."
    except httpx.ReadTimeout:
        yield "⚠️ [Timeout] Groq took too long to respond."