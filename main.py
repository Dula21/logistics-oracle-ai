from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.forecast import router as forecast_router
from routers.stream import router as stream_router
from routers.alerts import router as alerts_router

app = FastAPI()

# --- CRITICAL FIX: CORS CONFIGURATION ---
origins = [
    "http://localhost:3000",      # Local Next.js dev server
    "http://127.0.0.1:3000",    # Alternative local loopback address
    "http://192.168.100.151:3000" # Your exact LAN network address from Next.js logs
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Allows traffic from your frontend origins
    allow_credentials=True,
    allow_methods=["*"],              # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],              # Allows all custom/standard headers
)
# ----------------------------------------

# Register your routers
app.include_router(forecast_router)
app.include_router(stream_router)
app.include_router(alerts_router)