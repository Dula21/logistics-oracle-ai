import pandas as pd
import numpy as np

def generate_logistic_data():
    # 1. Create 2 years of daily data (2024-2025)
    # Why? Models need "history" to see "patterns".
    dates = pd.date_range(start='2024-01-01', end='2025-12-31', freq='D')
    
    # 2. Baseline sales (random noise)
    # We pretend this is an electronics SME in JAFZA
    base_sales = np.random.randint(15, 30, size=len(dates))
    
    # 3. Add Weekend Spikes (Saturdays are busy in Dubai retail)
    # Logic: If it's Saturday (day 5), add 15 sales
    weekday_effect = [15 if d.weekday() == 5 else 0 for d in dates]
    
    # 4. Add the "Ramadan Spike" 
    # Let's simulate a 30-day period where sales double
    ramadan_effect = [20 if (d.month == 3) else 0 for d in dates]
    
    total_sales = base_sales + weekday_effect + ramadan_effect
    
    # 5. Format for Prophet (Strict requirement: ds and y)
    df = pd.DataFrame({'ds': dates, 'y': total_sales})
    
    # Save it to a CSV so we can use it later
    df.to_csv('historic_sales.csv', index=False)
    print("✅ Success: 'historic_sales.csv' created with 731 days of data.")

if __name__ == "__main__":
    generate_logistic_data()