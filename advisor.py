import pandas as pd

def get_business_advice():
    # 1. Load the forecast we just made
    df = pd.read_csv('forecast_results.csv')
    
    # 2. Get the average predicted sales for the next 7 days
    next_week_avg = df.tail(7)['yhat'].mean()
    
    # 3. Create the "Context" for the AI
    # We are "painting a picture" for Llama 3.1
    data_summary = f"""
    UPCOMING FORECAST DATA:
    - Average Daily Sales Predicted: {round(next_week_avg, 2)} units.
    - Peak Prediction: {round(df['yhat'].max(), 2)} units.
    - Market Location: Dubai (JAFZA/D3).
    - Current Season: Post-Ramadan / Standard Retail.
    """
    
    # 4. The "Reasoning" Prompt
    prompt = f"""
    You are a Senior Logistics Consultant in Dubai. 
    Based on this data: {data_summary}
    
    Provide 3 specific 'Prescriptive Actions' for the warehouse manager.
    Focus on:
    1. Staffing (based on sales volume).
    2. Inventory (should they restock?).
    3. Delivery (mention specific Dubai logistics challenges).
    
    Keep it punchy and professional.
    """
    
    print("🤖 LOGIC READY. Sending data to the Oracle Advisor...")
    print("---")
    print(prompt)

if __name__ == "__main__":
    get_business_advice()