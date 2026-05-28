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

    # GUARDRAIL INTEGRATION: Wrapped system constraints into the prompt message context
    prompt_message = (
        f"System Role: You are an expert logistics analyzer engine. "
        f"Context: SKU {sku_id} has {stock} units left and is projected to stock out in exactly {days} days. "
        f"Operational Guardrails:\n"
        f"- Give a brief, sharp, 2-sentence action recommendation for a logistics team.\n"
        f"- Do not use markdown format tags.\n"
        f"- Stick entirely to physical inventory routing and procurement. Do not give general financial advice.\n"
        f"- CRITICAL: If days left is less than 7, your instructions must prioritize immediate reordering or urgent replenishment protocols."
    )
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_message,
        "stream": True
    }

    full_generated_text = ""
    timeout_config = httpx.Timeout(60.0, connect=5.0, read=60.0)

    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                if response.status_code != 200:
                    yield f"◈ [Engine Error] HTTP Status Code: {response.status_code}"
                    return

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        json_data = json.loads(line)
                        token = json_data.get("response", "")
                        if token:
                            full_generated_text += token
                            yield token
                    except Exception:
                        continue
                                
        # POST-STREAM OUTPUT GUARDRAIL:
        # If the timeline is critical (< 7 days) but the engine hallucinated soft or passive advice, 
        # we step in and append an absolute warning to protect operational metrics.
        if days < 7:
            text_upper = full_generated_text.upper()
            if any(w in text_upper for w in ["WAIT", "MONITOR", "DELAY", "STABLE", "SECURE"]):
                yield "\n⚠️ [Guardrail Override]: Current depletion runway is CRITICAL. Initiate immediate stock procurement procedures regardless of passive indicators."
                full_generated_text += " \n⚠️ [Guardrail Override]: Current depletion runway is CRITICAL. Initiate immediate stock procurement procedures regardless of passive indicators."

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