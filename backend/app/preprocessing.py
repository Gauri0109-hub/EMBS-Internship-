# =====================================================================
# MODULE: Data Preprocessing Pipeline (preprocessing.py)
# DESCRIPTION: Cleanses, validates, and engineers features for ML training.
#              Supports database tables, CSV, and Excel datasets.
# =====================================================================

import pandas as pd
import numpy as np
from datetime import datetime

def parse_date_safely(date_val):
    """
    Attempts to parse date strings using multiple standard formats.
    Returns string in 'YYYY-MM-DD' format if successful, else None.
    """
    if pd.isna(date_val):
        return None
        
    date_str = str(date_val).strip()
    
    # Try parsing Excel float timestamp first
    try:
        if date_str.replace('.', '', 1).isdigit():
            return pd.to_datetime(float(date_str), unit='D', origin='1899-12-30').strftime("%Y-%m-%d")
    except:
        pass
        
    # List of common formats to try
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y",
        "%Y/%m/%d", "%d-%b-%Y", "%d %B %Y", "%Y-%m-%d %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    # Fall back to pandas parser
    try:
        return pd.to_datetime(date_str).strftime("%Y-%m-%d")
    except:
        return None

def get_season_flags(month):
    """Identifies the three core Indian season flags."""
    is_summer = 1 if 2 <= month <= 5 else 0
    is_monsoon = 1 if 6 <= month <= 9 else 0
    is_winter = 1 if (month >= 10 or month == 1) else 0
    return is_summer, is_monsoon, is_winter

def validate_and_clean_sales_data(df):
    """
    Validates column presence, drops missing critical fields,
    standardizes names, and handles negative values.
    Expected columns: 'Date', 'Medicine Name', 'Quantity Sold'
    """
    # Clean column names (strip whitespace and convert case)
    df.columns = [str(c).strip() for c in df.columns]
    
    col_mapping = {
        "sale_date": ["date", "Date", "sale_date", "sale date", "Day", "day"],
        "medicine_name": ["medicine_name", "medicine name", "name", "Medicine Name", "Medicine", "medicine"],
        "quantity_sold": ["quantity_sold", "quantity sold", "quantity", "Quantity Sold", "Quantity", "qty", "Qty", "quantity_used", "quantity used"]
    }
    
    found_cols = {}
    for standard_col, variants in col_mapping.items():
        for var in variants:
            if var in df.columns:
                found_cols[standard_col] = var
                break
                
    missing_cols = [col for col in col_mapping.keys() if col not in found_cols]
    if missing_cols:
        raise ValueError(f"Missing required columns in sales data: {', '.join(missing_cols)}")
        
    # Standardize
    df = df.rename(columns={
        found_cols["sale_date"]: "sale_date",
        found_cols["medicine_name"]: "medicine_name",
        found_cols["quantity_sold"]: "quantity_sold"
    })
    
    # Keep only relevant columns
    df = df[["sale_date", "medicine_name", "quantity_sold"]].copy()
    
    # Handle missing values
    df = df.dropna(subset=["medicine_name", "quantity_sold"])
    
    # Clean data types
    df["medicine_name"] = df["medicine_name"].astype(str).str.strip()
    
    # Safe date parsing
    df["sale_date"] = df["sale_date"].apply(parse_date_safely)
    df = df.dropna(subset=["sale_date"])
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    
    # Handle negative / float sales
    df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce").fillna(0)
    df["quantity_sold"] = df["quantity_sold"].apply(lambda x: max(0, int(round(x))))
    
    return df

def validate_and_clean_inventory_data(df):
    """
    Validates and cleanses inventory data.
    Expected columns: 'Medicine Name', 'Current Stock', 'Expiry Date', 'Category', 'Supplier', 'Critical Medicine Flag'
    """
    df.columns = [str(c).strip() for c in df.columns]
    
    col_mapping = {
        "medicine_name": ["medicine_name", "medicine name", "name", "Medicine Name", "Medicine", "medicine"],
        "current_stock": ["current_stock", "current stock", "stock", "quantity", "Quantity", "Current Stock", "Stock"],
        "expiry_date": ["expiry_date", "expiry date", "expiry", "Expiry Date", "Expiry"]
    }
    
    found_cols = {}
    for standard_col, variants in col_mapping.items():
        for var in variants:
            if var in df.columns:
                found_cols[standard_col] = var
                break
                
    missing_cols = [col for col in col_mapping.keys() if col not in found_cols]
    if missing_cols:
        raise ValueError(f"Missing required columns in inventory data: {', '.join(missing_cols)}")
        
    df = df.rename(columns={
        found_cols["medicine_name"]: "medicine_name",
        found_cols["current_stock"]: "current_stock",
        found_cols["expiry_date"]: "expiry_date"
    })
    
    # Optional columns mapping
    opt_mapping = {
        "category": ["category", "Category", "type", "Type"],
        "supplier_name": ["supplier", "Supplier", "supplier_name", "Supplier Name"],
        "is_critical": ["is_critical", "critical", "Critical Medicine Flag", "is critical", "Critical?"]
    }
    for standard_col, variants in opt_mapping.items():
        for var in variants:
            if var in df.columns:
                df = df.rename(columns={var: standard_col})
                break
                
    # Clean columns
    df["medicine_name"] = df["medicine_name"].astype(str).str.strip()
    df = df.dropna(subset=["medicine_name"])
    
    # Current Stock cleaning
    df["current_stock"] = pd.to_numeric(df["current_stock"], errors="coerce").fillna(0)
    df["current_stock"] = df["current_stock"].apply(lambda x: max(0, int(round(x))))
    
    # Expiry Date cleaning
    df["expiry_date"] = df["expiry_date"].apply(parse_date_safely)
    # Default to 1 year if missing
    one_year_later = (datetime.now() + pd.Timedelta(days=365)).strftime("%Y-%m-%d")
    df["expiry_date"] = df["expiry_date"].fillna(one_year_later)
    
    # Optional columns defaults
    if "category" not in df.columns:
        df["category"] = "Uncategorized"
    else:
        df["category"] = df["category"].fillna("Uncategorized").astype(str).str.strip()
        
    if "supplier_name" not in df.columns:
        df["supplier_name"] = "Local Vendor"
    else:
        df["supplier_name"] = df["supplier_name"].fillna("Local Vendor").astype(str).str.strip()
        
    if "is_critical" not in df.columns:
        df["is_critical"] = "No"
    else:
        df["is_critical"] = df["is_critical"].fillna("No").astype(str).str.strip()
        df["is_critical"] = df["is_critical"].apply(lambda x: "Yes" if str(x).lower() in ["yes", "y", "1", "true"] else "No")
        
    return df

def build_continuous_timeline(sales_df):
    """
    Given a standardized sales dataframe for a medicine,
    constructs a continuous daily timeline, filling missing dates with 0.
    """
    if sales_df.empty:
        return pd.DataFrame()
        
    sales_df = sales_df.sort_values("sale_date")
    # Group by date to handle duplicate entries on same day
    daily_sales = sales_df.groupby("sale_date")["quantity_sold"].sum().reset_index()
    daily_sales.set_index("sale_date", inplace=True)
    
    # Reindex to fill all intermediate days
    full_range = pd.date_range(start=daily_sales.index.min(), end=daily_sales.index.max(), freq="D")
    daily_sales = daily_sales.reindex(full_range, fill_value=0)
    
    daily_sales = daily_sales.reset_index().rename(columns={"index": "date"})
    return daily_sales

def engineer_features(df):
    """
    Computes time-series and calendar features from date column.
    Adds month, day_of_week, seasonal flags, and rolling averages.
    """
    if df.empty:
        return df
        
    df_feat = df.copy()
    df_feat["month"] = df_feat["date"].dt.month
    df_feat["day_of_week"] = df_feat["date"].dt.dayofweek
    
    seasons = [get_season_flags(m) for m in df_feat["month"]]
    df_feat["is_summer"] = [s[0] for s in seasons]
    df_feat["is_monsoon"] = [s[1] for s in seasons]
    df_feat["is_winter"] = [s[2] for s in seasons]
    
    # 7-day rolling average (lag feature)
    df_feat["rolling_avg"] = df_feat["quantity_sold"].rolling(window=7, min_periods=1).mean()
    
    return df_feat
