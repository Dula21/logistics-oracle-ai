from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from advisor import get_business_advice

app = FastAPI()

# Allow your Next.js app (on port 3000) to talk to your FastAPI app (on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/forecast")
def get_forecast_data():
    df = pd.read_csv('forecast_results.csv')
    recent_df = df.tail(14).copy()
    
    # Clean up dates format from 2026-05-16 to "May 16"
    clean_dates = pd.to_datetime(recent_df['ds']).dt.strftime('%b %d').tolist()
    
    # Zip data together into an array of objects matching the frontend chart needs
    chart_rows = []
    for _, row in recent_df.iterrows():
        chart_rows.append({
            "predicted": int(round(row['yhat'])),
            "lower": int(round(row['yhat_lower'])),
            "upper": int(round(row['yhat_upper']))
        })
    
    return {
        "dates": clean_dates,
        "rows": chart_rows,
        "avg_sales": int(round(recent_df['yhat'].mean())),
        "advice": get_business_advice()
    }