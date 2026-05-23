import csv
import random
from datetime import datetime, timedelta

def generate_dubai_logistics_data():
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    
    skus = ["A1023", "B5421", "C9011"]
    
    # Ramadan 2025 in UAE fell roughly between March 1 and March 30, 2025
    ramadan_start_2025 = datetime(2025, 3, 1)
    ramadan_end_2025 = datetime(2025, 3, 30)
    
    # Ramadan 2024 fell roughly between March 11 and April 9, 2024
    ramadan_start_2024 = datetime(2024, 3, 11)
    ramadan_end_2024 = datetime(2024, 4, 9)

    filename = "historic_sales.csv"
    
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Perfect feature mapping for time-series predictions
        writer.writerow(["Date", "SKU_ID", "Sales_Units", "Promo_Active", "Ramadan", "Stock_On_Hand"])
        
        for sku in skus:
            # Seed distinct tracking starting points for varied stock profiles
            current_stock = random.randint(300, 500)
            current_date = start_date
            
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                
                # Establish contextual feature flags
                is_ramadan = 0
                if (ramadan_start_2024 <= current_date <= ramadan_end_2024) or \
                   (ramadan_start_2025 <= current_date <= ramadan_end_2025):
                    is_ramadan = 1
                    
                # Weekend promotions (Friday/Saturday/Sunday spikes standard for JAFZA/D3 e-commerce)
                is_promo = 1 if (current_date.weekday() in [4, 5, 6] and random.random() > 0.4) else 0
                
                # Base math engine calculations
                base_sales = random.randint(15, 35)
                if is_promo:
                    base_sales = int(base_sales * 1.5)
                if is_ramadan:
                    base_sales = int(base_sales * 1.8) # Strong seasonal distribution swing
                    
                sales_units = max(0, base_sales)
                
                # Stock depletion simulation loop
                current_stock -= sales_units
                
                # Automated wholesale procurement reorder triggers
                if current_stock <= 50:
                    current_stock += random.randint(350, 500)
                    
                writer.writerow([date_str, sku, sales_units, is_promo, is_ramadan, current_stock])
                current_date += timedelta(days=1)
                
    print(f"Successfully generated 2024-2025 logistics data ledger: '{filename}'")

if __name__ == "__main__":
    generate_dubai_logistics_data()