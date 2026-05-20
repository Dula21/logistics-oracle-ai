import os
import httpx
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3.2")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/api/generate")

_advice_cache = {}

async def stream_advice(sku_id: str, days: int, stock: int):
    cache_key = f"{sku_id}_{days}_{stock}"
    
    # 1. Cache hit abstraction layer
    if cache_key in _advice_cache:
        cached_text = _advice_cache[cache_key]
        words = cached_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.01)
        return

    prompt_message = (
        f"You are an expert logistics analyzer. SKU {sku_id} has {stock} units left "
        f"and is projected to stock out in exactly {days} days. Give a brief, sharp, "
        f"2-sentence action recommendation for a logistics team. Do not use markdown format tags."
    )
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_message,
        "stream": True
    }

    full_generated_text = ""
    
    # FIX 2: Create a dedicated timeout configuration matrix. 
    # Gives the LLM up to 60 seconds to process headers, while keeping connect times tight.
    timeout_config = httpx.Timeout(60.0, connect=5.0, read=60.0)

    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                if response.status_code != 200:
                    yield f"◈ [Engine Error] HTTP Status Code: {response.status_code}"
                    return

                # FIX 1: Use aiter_text() instead of iter_text() for proper async streaming
                async_text_iterator = response.aiter_text()
                
                async for chunk in async_text_iterator:
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
                            except Exception:
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
            f"The local LLM engine took too long to generate an advisory token sequence. "
            f"Check your local hardware utilization metrics."
        )