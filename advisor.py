import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

# Load secrets from the .env file
load_dotenv()

# Initialize the Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_business_advice():
    # 1. Load the forecast
    df = pd.read_csv('forecast_results.csv')
    next_week_avg = df.tail(7)['yhat'].mean()
    
    # 2. Build the context
    data_summary = f"Predicted daily sales for next week: {round(next_week_avg, 2)} units."

    # 3. Call the "Brain" (Llama 3.1)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a professional Dubai logistics consultant. Provide 3 sharp, prescriptive business actions."
            },
            {
                "role": "user",
                "content": f"Based on this sales forecast: {data_summary}, what should the warehouse manager do?"
            }
        ],
        temperature=0.5, # Keeps it professional, not too creative
    )
    
    # 4. Return the actual AI words
    return completion.choices[0].message.content

if __name__ == "__main__":
    print("🤖 The Oracle is thinking...")
    print(get_business_advice())