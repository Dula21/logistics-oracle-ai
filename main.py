from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 1. Import your routers cleanly
from routers.forecast import router as forecast_router
from routers.stream import router as stream_router


app = FastAPI(title="Dubai Logistics Oracle SME Engine")

# 2. Enable CORS so your Next.js frontend (port 3000) can communicate with your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; narrow this down to your frontend port in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. REGISTER THE ROUTERS WITH FASTAPI
app.include_router(forecast_router)
app.include_router(stream_router)


@app.get("/")
def read_root():
    return {"status": "Online", "engine": "FastAPI Core Matrix Active"}