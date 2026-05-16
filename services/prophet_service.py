from prophet import Prophet
import pandas as pd

def run_prophet_engine(df_raw, periods=14):
    # Format columns explicitly for Prophet's fit signature
    df_input = df_raw.rename(columns={"Date": "ds", "Sales_Units": "y"})
    
    # Initialize model with your core contextual features
    model = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
    
    if "Ramadan" in df_input.columns and df_input["Ramadan"].sum() > 0:
        model.add_regressor("Ramadan")
    if "Promo_Active" in df_input.columns and df_input["Promo_Active"].sum() > 0:
        model.add_regressor("Promo_Active")
        
    model.fit(df_input)
    
    # Predict the mathematical sequence
    future = model.make_future_dataframe(periods=periods)
    if "Ramadan" in df_input.columns:
        future["Ramadan"] = 0
    if "Promo_Active" in df_input.columns:
        future["Promo_Active"] = 0
        
    forecast = model.predict(future)
    return forecast.tail(periods)