from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import asyncio

from routers.forecast import router as forecast_router
from routers.stream import router as stream_router
from routers.upload import router as upload_router

# SKUs to pre-warm on startup
WATCHLIST = ["A1023", "B5421", "C9011"]
BASE_URL = "http://localhost:8000"


async def prewarm_cache():
    """
    Silently calls all endpoints for every SKU on startup.
    By the time the browser opens, cache is full and responses are instant.
    """
    await asyncio.sleep(2)  # Wait for server to fully bind first

    async with httpx.AsyncClient(timeout=180.0) as client:
        for sku in WATCHLIST:
            # 1. Warm operational forecast (dashboard charts)
            try:
                await client.get(f"{BASE_URL}/api/forecast?sku={sku}")
                print(f"[Cache] ✓ forecast warmed for {sku}")
            except Exception as e:
                print(f"[Cache] ✗ forecast failed for {sku}: {e}")

            # 2. Warm insights data (2-year chart)
            try:
                r = await client.get(f"{BASE_URL}/api/insights?sku={sku}")
                data = r.json()
                meta = data.get("insights_metadata", {})
                forecast = data.get("forecast", [])

                ramadan = meta.get("ramadan_impact_factor", 1.8)
                promo = meta.get("promo_impact_factor", 1.3)
                points = meta.get("historical_data_points", 0)

                # Calculate avg from 2025 rows
                rows_2025 = [f for f in forecast if f["date"].startswith("2025")]
                avg = (
                    sum(r["predicted_units"] for r in rows_2025) / len(rows_2025)
                    if rows_2025 else 0.0
                )

                print(f"[Cache] ✓ insights warmed for {sku}")

                # 3. Warm Llama dashboard stream
                async with client.stream(
                    "GET",
                    f"{BASE_URL}/api/stream?sku={sku}&days=14&stock=150"
                ) as stream:
                    async for _ in stream.aiter_text():
                        pass
                print(f"[Cache] ✓ dashboard Llama warmed for {sku}")

                # 4. Warm Llama insights stream
                async with client.stream(
                    "GET",
                    f"{BASE_URL}/api/stream/insights?sku={sku}"
                    f"&ramadan_factor={ramadan}&promo_factor={promo}"
                    f"&avg_daily_sales={avg:.1f}&data_points={points}"
                ) as stream:
                    async for _ in stream.aiter_text():
                        pass
                print(f"[Cache] ✓ insights Llama warmed for {sku}")

            except Exception as e:
                print(f"[Cache] ✗ insights/llama failed for {sku}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only run the heavy pre-warm cache if running on a local development machine
    if os.getenv("RENDER") is None: 
        print("[Cache] Dev machine detected. Starting background pre-warm...")
        asyncio.create_task(prewarm_cache())
    else:
        print("[Cache] Production Cloud detected. Skipping background local loops to optimize memory.")
    yield


app = FastAPI(
    title="Dubai Logistics Oracle SME Engine",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast_router)
app.include_router(stream_router)
app.include_router(upload_router)


@app.get("/")
def read_root():
    return {"status": "Online", "engine": "FastAPI Core Matrix Active"}