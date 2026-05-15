import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt

def train_and_forecast():
    # 1. Load the data we just created
    df = pd.read_csv('historic_sales.csv')

    # 2. Initialize the Prophet model
    # We tell it to look for yearly and weekly patterns
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True)

    # 3. Training (The "Learning" Phase)
    print("🧠 The Brain is analyzing 2 years of Dubai sales data...")
    model.fit(df)

    # 4. Create a "Future" timeline
    # We want to predict the next 30 days (January 2026)
    future = model.make_future_dataframe(periods=30)

    # 5. Predict!
    forecast = model.predict(future)

    # 6. Save the results
    # We only care about the date (ds), the prediction (yhat), 
    # and the lower/upper bounds (uncertainty)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv('forecast_results.csv', index=False)
    
    print("🔮 Prediction Complete! Results saved to 'forecast_results.csv'")

    # Optional: See the trends (Visual proof)
    # This shows you the Ramadan spike and Saturday rush the AI "discovered"
    fig = model.plot_components(forecast)
    plt.savefig('trends.png')
    print("📈 Trend analysis saved as 'trends.png'")

if __name__ == "__main__":
    train_and_forecast()