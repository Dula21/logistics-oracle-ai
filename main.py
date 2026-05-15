from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from advisor import get_business_advice
import json

app = FastAPI()

# CRITICAL: This allows your Next.js app (on port 3000) 
# to talk to your FastAPI app (on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/forecast")
def get_forecast_data():
    df = pd.read_csv('forecast_results.csv')
    recent_df = df.tail(14)
    
    return {
        "dates": recent_df['ds'].tolist(),
        "values": [round(v, 2) for v in recent_df['yhat'].tolist()],
        "avg_sales": round(recent_df['yhat'].mean(), 2),
        "advice": get_business_advice()
    }