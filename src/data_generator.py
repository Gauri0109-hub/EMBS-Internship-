# =====================================================================
# PROJECT: Smart Pharmacy Inventory Prediction System
# MODULE: Enhanced Data Generator (data_generator.py)
# DESCRIPTION: Creates realistic synthetic datasets representing 25 medicines
#             across 365 days (9,125 rows of history) with additional fields:
#             supplier_name, seasonal_demand_pattern, and critical flags.
#
# EXPLAINER FOR BEGINNERS:
# - What this does: It creates our "database" consisting of two CSV files.
# - Why it is used: An AI system is only as good as its data. We simulate realistic
#   seasonal disease waves (Monsoon, Winter, Summer) so that the machine learning
#   model has high-quality patterns to learn from.
# - How to understand: It defines a master list of 25 medical formulations and uses
#   date calculations (timedelta) to iterate day-by-day, adding random statistical
#   fluctuations (noise) to daily sales.
# =====================================================================

import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create 'data' directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Master database of 25 medicines with advanced fields
# - seasonal_demand_pattern: "Monsoon Spike", "Winter Spike", "Summer Spike", "Constant"
# - supplier_name: Selected Indian pharmaceutical suppliers
medicine_master = [
    {
        "medicine_name": "Paracetamol 650mg",
        "bilingual_name": "पॅरासिटामॉल ६५०mg",
        "category": "Analgesic (Fever & Pain)",
        "base_usage": 16,
        "unit_price": 2.50,
        "is_critical": "No",
        "supplier_name": "Maurya Pharma Distributors",
        "seasonal_demand_pattern": "Monsoon Spike",
        "seasonality": {"Summer": 1.0, "Monsoon": 2.8, "Winter": 1.2}
    },
    {
        "medicine_name": "Cetirizine 10mg",
        "bilingual_name": "सेटिरिझिन १०mg",
        "category": "Antihistamine (Allergies)",
        "base_usage": 10,
        "unit_price": 3.00,
        "is_critical": "No",
        "supplier_name": "Sahyadri Medical Logistics",
        "seasonal_demand_pattern": "Monsoon Spike",
        "seasonality": {"Summer": 1.1, "Monsoon": 2.2, "Winter": 1.4}
    },
    {
        "medicine_name": "Amoxicillin 500mg",
        "bilingual_name": "अमॉक्सिसिलिन ५००mg",
        "category": "Antibiotic (Infections)",
        "base_usage": 12,
        "unit_price": 8.50,
        "is_critical": "No",
        "supplier_name": "Bharat Biotech Supply",
        "seasonal_demand_pattern": "Monsoon Spike",
        "seasonality": {"Summer": 0.8, "Monsoon": 2.0, "Winter": 1.3}
    },
    {
        "medicine_name": "Insulin Glargine 100IU",
        "bilingual_name": "इन्सुलिन ग्लार्जिन १००IU",
        "category": "Antidiabetic (Critical)",
        "base_usage": 5,
        "unit_price": 145.00,
        "is_critical": "Yes",
        "supplier_name": "Eli Lilly India Ltd.",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.0}
    },
    {
        "medicine_name": "Salbutamol Inhaler",
        "bilingual_name": "साल्ब्युटामॉल इनहेलर",
        "category": "Respiratory (Asthma)",
        "base_usage": 4,
        "unit_price": 95.00,
        "is_critical": "Yes",
        "supplier_name": "Cipla Pharmaceuticals",
        "seasonal_demand_pattern": "Winter Spike",
        "seasonality": {"Summer": 0.7, "Monsoon": 1.5, "Winter": 2.6}
    },
    {
        "medicine_name": "Phenytoin 100mg",
        "bilingual_name": "फेनिटॉइन १००mg",
        "category": "Anticonvulsant (Epilepsy)",
        "base_usage": 3,
        "unit_price": 15.00,
        "is_critical": "Yes",
        "supplier_name": "Abbott India Ltd.",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.0}
    },
    {
        "medicine_name": "ORS (Oral Rehydration)",
        "bilingual_name": "ओ.आर.एस (जलसंजीवनी)",
        "category": "Rehydration (Dehydration)",
        "base_usage": 22,
        "unit_price": 4.50,
        "is_critical": "No",
        "supplier_name": "FDC India Distributors",
        "seasonal_demand_pattern": "Summer Spike",
        "seasonality": {"Summer": 3.2, "Monsoon": 1.4, "Winter": 0.4}
    },
    {
        "medicine_name": "Cough Syrup 100ml",
        "bilingual_name": "खोखल्याचे औषध १००ml",
        "category": "Respiratory (Cough/Cold)",
        "base_usage": 9,
        "unit_price": 45.00,
        "is_critical": "No",
        "supplier_name": "Dabur Medical Agency",
        "seasonal_demand_pattern": "Winter Spike",
        "seasonality": {"Summer": 0.5, "Monsoon": 1.3, "Winter": 3.0}
    },
    {
        "medicine_name": "Pantoprazole 40mg",
        "bilingual_name": "पॅन्टोप्राझोल ४०mg",
        "category": "Antacid (Acidity)",
        "base_usage": 15,
        "unit_price": 6.00,
        "is_critical": "No",
        "supplier_name": "Sun Pharma Industries",
        "seasonal_demand_pattern": "Summer Spike",
        "seasonality": {"Summer": 1.5, "Monsoon": 1.0, "Winter": 0.8}
    },
    {
        "medicine_name": "Metformin 500mg",
        "bilingual_name": "मेटफॉर्मिन ५००mg",
        "category": "Antidiabetic",
        "base_usage": 18,
        "unit_price": 3.50,
        "is_critical": "No",
        "supplier_name": "Lupin India Ltd.",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.0}
    },
    {
        "medicine_name": "Amlodipine 5mg",
        "bilingual_name": "अॅम्लोडिपिन ५mg",
        "category": "Cardiovascular (BP)",
        "base_usage": 14,
        "unit_price": 2.00,
        "is_critical": "No",
        "supplier_name": "Torrent Pharmaceuticals",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.1}
    },
    {
        "medicine_name": "Azithromycin 500mg",
        "bilingual_name": "अझिथ्रोमायसिन ५००mg",
        "category": "Antibiotic (Infections)",
        "base_usage": 6,
        "unit_price": 22.00,
        "is_critical": "No",
        "supplier_name": "Alkem Laboratories Ltd.",
        "seasonal_demand_pattern": "Winter Spike",
        "seasonality": {"Summer": 0.7, "Monsoon": 1.4, "Winter": 1.8}
    },
    {
        "medicine_name": "Ibuprofen 400mg",
        "bilingual_name": "आयबूप्रोफेन ४००mg",
        "category": "Analgesic (Fever & Pain)",
        "base_usage": 8,
        "unit_price": 1.80,
        "is_critical": "No",
        "supplier_name": "Maurya Pharma Distributors",
        "seasonal_demand_pattern": "Monsoon Spike",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.4, "Winter": 1.1}
    },
    {
        "medicine_name": "Zinc Tablets 20mg",
        "bilingual_name": "झिंक गोळ्या २०mg",
        "category": "Supplement (Diarrhea)",
        "base_usage": 10,
        "unit_price": 4.00,
        "is_critical": "No",
        "supplier_name": "Sahyadri Medical Logistics",
        "seasonal_demand_pattern": "Monsoon Spike",
        "seasonality": {"Summer": 1.2, "Monsoon": 2.4, "Winter": 0.9}
    },
    {
        "medicine_name": "Multivitamin Complex",
        "bilingual_name": "मल्टीव्हिटॅमिन कॉम्प्लेक्स",
        "category": "Supplement (Nutrition)",
        "base_usage": 12,
        "unit_price": 5.50,
        "is_critical": "No",
        "supplier_name": "Himalaya Wellness Corp.",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.0}
    },
    {
        "medicine_name": "Folic Acid 5mg",
        "bilingual_name": "फॉलिक ॲसिड ५mg",
        "category": "Supplement (Nutrition)",
        "base_usage": 15,
        "unit_price": 1.20,
        "is_critical": "No",
        "supplier_name": "Bharat Biotech Supply",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.0}
    },
    {
        "medicine_name": "Atorvastatin 10mg",
        "bilingual_name": "अ‍ॅटोर्वास्टेटिन १०mg",
        "category": "Cardiovascular (Cholesterol)",
        "base_usage": 11,
        "unit_price": 7.80,
        "is_critical": "No",
        "supplier_name": "Sun Pharma Industries",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.0}
    },
    {
        "medicine_name": "Levocetirizine 5mg",
        "bilingual_name": "लेव्होसेटिरिझिन ५mg",
        "category": "Antihistamine (Allergies)",
        "base_usage": 8,
        "unit_price": 2.80,
        "is_critical": "No",
        "supplier_name": "Cipla Pharmaceuticals",
        "seasonal_demand_pattern": "Winter Spike",
        "seasonality": {"Summer": 0.6, "Monsoon": 1.3, "Winter": 2.0}
    },
    {
        "medicine_name": "Ranitidine 150mg",
        "bilingual_name": "रॅानिटिडिन १५०mg",
        "category": "Antacid (Acidity)",
        "base_usage": 16,
        "unit_price": 1.50,
        "is_critical": "No",
        "supplier_name": "Abbott India Ltd.",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.1, "Monsoon": 1.0, "Winter": 0.9}
    },
    {
        "medicine_name": "Diclofenac Gel 30g",
        "bilingual_name": "डायक्लोफेनॅक जेल ३०g",
        "category": "Analgesic (Fever & Pain)",
        "base_usage": 6,
        "unit_price": 35.00,
        "is_critical": "No",
        "supplier_name": "Maurya Pharma Distributors",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.1}
    },
    {
        "medicine_name": "ORS (Orange Flavor)",
        "bilingual_name": "ओ.आर.एस (संत्री स्वाद)",
        "category": "Rehydration (Dehydration)",
        "base_usage": 15,
        "unit_price": 5.00,
        "is_critical": "No",
        "supplier_name": "FDC India Distributors",
        "seasonal_demand_pattern": "Summer Spike",
        "seasonality": {"Summer": 2.8, "Monsoon": 1.2, "Winter": 0.5}
    },
    {
        "medicine_name": "Dolo 650mg",
        "bilingual_name": "डोलो ६५०mg",
        "category": "Analgesic (Fever & Pain)",
        "base_usage": 20,
        "unit_price": 2.00,
        "is_critical": "No",
        "supplier_name": "Micro Labs Ltd.",
        "seasonal_demand_pattern": "Monsoon Spike",
        "seasonality": {"Summer": 1.0, "Monsoon": 2.6, "Winter": 1.2}
    },
    {
        "medicine_name": "Erythromycin 250mg",
        "bilingual_name": "एरिथ्रोमायसिन २५०mg",
        "category": "Antibiotic (Infections)",
        "base_usage": 7,
        "unit_price": 11.50,
        "is_critical": "No",
        "supplier_name": "Alkem Laboratories Ltd.",
        "seasonal_demand_pattern": "Monsoon Spike",
        "seasonality": {"Summer": 0.9, "Monsoon": 1.6, "Winter": 1.2}
    },
    {
        "medicine_name": "Montelukast 10mg",
        "bilingual_name": "मॉन्टील्यूकास्ट १०mg",
        "category": "Respiratory (Asthma)",
        "base_usage": 6,
        "unit_price": 14.50,
        "is_critical": "Yes",
        "supplier_name": "Cipla Pharmaceuticals",
        "seasonal_demand_pattern": "Winter Spike",
        "seasonality": {"Summer": 0.7, "Monsoon": 1.4, "Winter": 2.2}
    },
    {
        "medicine_name": "Carbamazepine 200mg",
        "bilingual_name": "कार्बामाझेपिन २००mg",
        "category": "Anticonvulsant (Epilepsy)",
        "base_usage": 4,
        "unit_price": 8.00,
        "is_critical": "Yes",
        "supplier_name": "Abbott India Ltd.",
        "seasonal_demand_pattern": "Constant",
        "seasonality": {"Summer": 1.0, "Monsoon": 1.0, "Winter": 1.0}
    }
]

def get_season(date_obj):
    month = date_obj.month
    if 2 <= month <= 5:
        return "Summer"
    elif 6 <= month <= 9:
        return "Monsoon"
    else:
        return "Winter"

def generate_datasets():
    print("Generating comprehensive simulated pharmacy inventory datasets...")
    
    # Establish Timeline: Last 365 Days ending today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    history_data = []
    
    np.random.seed(42)
    random.seed(42)
    
    current_date = start_date
    while current_date <= end_date:
        season = get_season(current_date)
        
        for med in medicine_master:
            base = med["base_usage"]
            multiplier = med["seasonality"][season]
            
            # Poisson distribution to model realistic counts of sales transactions
            daily_mean = base * multiplier
            quantity_used = np.random.poisson(daily_mean)
            quantity_used = max(1, int(quantity_used))
            
            history_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "medicine_name": med["medicine_name"],
                "quantity_used": quantity_used,
                "season": season,
                "day_of_week": current_date.weekday(),
                "month": current_date.month
            })
            
        current_date += timedelta(days=1)
        
    history_df = pd.DataFrame(history_data)
    history_df.to_csv("data/daily_usage_history.csv", index=False)
    print(f"Daily usage history saved to data/daily_usage_history.csv with {len(history_df)} entries.")
    
    # Generate Current Inventory
    inventory_data = []
    
    for i, med in enumerate(medicine_master):
        med_id = f"MED{i+1:03d}"
        
        # Induce deliberate low stocks on critical drugs to demonstrate red alerts:
        if med["medicine_name"] == "Insulin Glargine 100IU":
            current_stock = 12  # Lasts only ~2 days
        elif med["medicine_name"] == "Salbutamol Inhaler":
            current_stock = 16  # Lasts only ~4 days
        elif med["medicine_name"] == "Carbamazepine 200mg":
            current_stock = 14  # Lasts only ~3 days
        elif med["medicine_name"] == "ORS (Oral Rehydration)":
            current_stock = 450 # Well stocked
        elif med["medicine_name"] == "Cetirizine 10mg":
            current_stock = 30  # Low stock
        else:
            # Average stock: 7x to 25x daily baseline demand
            current_stock = random.randint(7 * med["base_usage"], 25 * med["base_usage"])
            
        min_required_stock = int(med["base_usage"] * 8) # Safety reorder point
        
        # Force expiry dates to test warnings:
        if med["medicine_name"] == "Pantoprazole 40mg":
            # Expiring soon
            expiry = datetime.now() + timedelta(days=18)
        elif med["medicine_name"] == "Zinc Tablets 20mg":
            # Expired
            expiry = datetime.now() - timedelta(days=6)
        else:
            expiry = datetime.now() + timedelta(days=random.randint(350, 900))
            
        inventory_data.append({
            "medicine_id": med_id,
            "medicine_name": med["medicine_name"],
            "bilingual_name": med["bilingual_name"],
            "category": med["category"],
            "current_stock": current_stock,
            "min_required_stock": min_required_stock,
            "expiry_date": expiry.strftime("%Y-%m-%d"),
            "is_critical": med["is_critical"],
            "unit_price": med["unit_price"],
            "supplier_name": med["supplier_name"],
            "seasonal_demand_pattern": med["seasonal_demand_pattern"]
        })
        
    inventory_df = pd.DataFrame(inventory_data)
    inventory_df.to_csv("data/medicine_inventory.csv", index=False)
    print(f"Current inventory saved to data/medicine_inventory.csv with {len(inventory_df)} items.")
    print("Dataset generation completed! Database ready for multipage app.")

if __name__ == "__main__":
    generate_datasets()
