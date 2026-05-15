from fastapi import FastAPI
import pandas as pd
from advisor import get_business_advice # We are importing your logic!

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to the Dubai Logistics Oracle API"}

@app.get("/forecast-summary")
def get_summary():
    # 1. Load the forecast we created with the Brain
    try:
        df = pd.read_csv('forecast_results.csv')
        
        # 2. Pick some key numbers to show the user
        latest_prediction = df.iloc[-1]
        
        return {
            "target_date": latest_prediction['ds'],
            "predicted_sales": round(latest_prediction['yhat'], 2),
            "status": "Success",
            "location": "JAFZA / Dubai"
        }
    except FileNotFoundError:
        return {"error": "Forecast data not found. Please run brain.py first."}

@app.get("/get-advice")
def advisor_endpoint():
    # This runs your advisor logic and returns it via the web
    advice = get_business_advice()
    return {"oracle_advice": "Advice generated. Check terminal (Groq integration next!)"}