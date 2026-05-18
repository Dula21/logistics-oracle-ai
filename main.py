from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.forecast import router as forecast_router
from routers.stream import router as stream_router
from routers.alerts import router as alerts_router

app = FastAPI(title="Logistics Oracle Pipeline Architecture")

# Configure CORS so your Next.js dashboard can connect securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fix your 404s by routing everything through the global '/api' path
app.include_router(forecast_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)