import httpx
import json
from typing import AsyncGenerator

OLLAMA_URL = "http://localhost:11434/api/generate"

async def stream_advice(sku_id: str, days: int, stock: int) -> AsyncGenerator[str, None]:
    """
    Connects to local Ollama instance and streams real-time token chunks
    to provide regional logistics advice.
    """
    # Dynamic context injection based on our generated patterns
    seasonal_context = ""
    if sku_id == "C9011":
        seasonal_context = "This item experiences massive holiday demand surges (+90%) during Ramadan retail hours."
    elif sku_id == "B5842":
        seasonal_context = "This item typically encounters a -20% sales volume drop during active Ramadan fasting windows."

    prompt = f"""
    You are a logistics and inventory planning optimization engine for a Dubai SME supply chain hub.
    Target SKU: {sku_id}
    Current Warehouse Stock: {stock} units
    Velocity Runway Projection: Will fully stock out in exactly {days} days.
    Regional Context Variables: {seasonal_context} Focus on JAFZA logistics channels, UAE weekends (Friday/Saturday demand spikes), or regional trade windows.
    
    Task: Provide a sharp, data-driven 2-sentence executive operational instruction. 
    Be direct. Do not say "Here is the recommendation". Speak directly as the system advisor.
    """
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream("POST", OLLAMA_URL, json={
                "model": "llama3.1",
                "prompt": prompt,
                "stream": True,
            }) as resp:
                if resp.status_code != 200:
                    yield f"⚠️ Advisor core returned a status fault: {resp.status_code}"
                    return

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except httpx.ConnectError:
            # Fallback if Ollama is not actively running in the background
            yield f"◈ [Local Core Offline] Alert status on {sku_id} indicates {days} days of stock remaining. Suggest immediate reorder review."