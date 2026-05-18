import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Baking realistic logistics dataset...")

# 1. Set timeline parameters (Covering late 2024 through mid-2026 to capture multiple seasons)
start_date = datetime(2024, 10, 1)
total_days = 600
date_list = [start_date + timedelta(days=x) for x in range(total_days)]

# 2. Define our 3 target SKUs with distinct baseline behaviors
# In UAE logistics, Friday and Saturday see massive retail supply distributions
products = {
    "A1023": {"base": 35, "weekend_bump": 18, "ramadan_multiplier": 1.4, "starting_stock": 420},
    "B5842": {"base": 75, "weekend_bump": 35, "ramadan_multiplier": 0.8, "starting_stock": 850}, # B5842 slows down during Ramadan fasting hours
    "C9011": {"base": 15, "weekend_bump": 5,  "ramadan_multiplier": 1.9, "starting_stock": 250}  # C9011 spikes drastically during Ramadan (e.g., Dates/Beverages)
}

# 3. Dynamic Ramadan Tracker Windows (Since Ramadan shifts ~11 days earlier every year)
def check_ramadan(dt):
    # 2025 true Ramadan window: Approx March 1 to March 30
    if dt.year == 2025 and dt.month == 3 and (1 <= dt.day <= 30):
        return 1
    # 2026 true Ramadan window: Approx February 18 to March 19
    if dt.year == 2026 and (
        (dt.month == 2 and dt.day >= 18) or (dt.month == 3 and dt.day <= 19)
    ):
        return 1
    return 0

all_records = []

for sku, matrix in products.items():
    # Set the starting stock simulation anchor point
    current_inventory = matrix["starting_stock"]
    
    for current_date in date_list:
        # Determine day of week rules (4 = Friday, 5 = Saturday)
        is_weekend = 1 if current_date.weekday() in [4, 5] else 0
        is_ramadan = check_ramadan(current_date)
        
        # System promotional events (Simulating payday spikes on the 1st and 28th of every month)
        is_promo = 1 if current_date.day in [1, 28] else 0
        
        # Calculate algorithmic sales baseline volume
        sales_volume = matrix["base"]
        
        # Add weekend distribution trends
        if is_weekend:
            sales_volume += matrix["weekend_bump"]
            
        # Multiply by holiday weightings
        if is_ramadan:
            sales_volume = int(sales_volume * matrix["ramadan_multiplier"])
            
        # Add flat promo velocity spike
        if is_promo:
            sales_volume += 25
            
        # Inject standard random white-noise fluctuation (realism variance)
        noise = np.random.randint(-5, 6)
        daily_sales = max(2, int(sales_volume + noise))
        
        # Deplete warehouse stock levels based on sales execution loops
        current_inventory -= daily_sales
        
        # Automated standard procurement replenishment simulation trigger
        if current_inventory < (matrix["starting_stock"] * 0.15):
            current_inventory += matrix["starting_stock"] # Stock truck arrival simulation
            
        all_records.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "SKU_ID": sku,
            "Sales_Units": daily_sales,
            "Promo_Active": is_promo,
            "Ramadan": is_ramadan,
            "Stock_On_Hand": current_inventory
        })

# 4. Save out cleanly to workspace disk
df = pd.DataFrame(all_records)
df.to_csv("historic_sales.csv", index=False)

print(f"🎉 Successfully built 'historic_sales.csv' with {len(df)} lines of high-fidelity logs!")