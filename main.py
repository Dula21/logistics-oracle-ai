from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import pandas as pd
from advisor import get_business_advice
import json

app = FastAPI()

# Standard initialization
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # 1. Load data
    df = pd.read_csv('forecast_results.csv')
    recent_df = df.tail(14)
    
    # 2. Prepare data for Chart.js
    dates_list = recent_df['ds'].tolist()
    values_list = [round(v, 2) for v in recent_df['yhat'].tolist()]
    avg_val = round(sum(values_list) / len(values_list), 2)
    
    # 3. Get AI advice
    ai_advice = get_business_advice()
    
    # 4. Prepare your context (excluding request here)
    context_data = {
        "avg_sales": avg_val, 
        "advice": ai_advice,
        "dates": json.dumps(dates_list),
        "values": json.dumps(values_list)
    }
    
    # 5. The "Standard" FastAPI way to call the template
    # We pass the request, the filename, and the context dictionary separately
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context=context_data
    )