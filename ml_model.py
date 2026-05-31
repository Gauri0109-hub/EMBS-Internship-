# =====================================================================
# PROJECT: Smart Pharmacy Inventory Prediction System
# MODULE: Machine Learning Engine (ml_model.py)
# DESCRIPTION: Trains Linear Regression and Random Forest models on
#             historical sales data, predicts future daily demand,
#             and calculates stock-out dates.
#
# EXPLAINER FOR BEGINNERS:
# - Machine Learning (ML): We teach the computer to find patterns in past data
#   (like seasonality) and use those patterns to predict future actions.
# - Linear Regression: A simple model that fits a straight line through the data.
#   It is extremely fast and very easy to explain using formula weights!
#   Formula: Demand = (W1 * Month) + (W2 * DayOfWeek) + (W3 * Season) + Intercept
# - Random Forest Regressor: A collection of Decision Trees. It is a bit more advanced,
#   great for catching non-linear curves (like a sudden spike in a specific month).
# - Feature Engineering: The process of creating input variables (features) for our model.
#   We use features like Day of the Week, Month, and Season flags.
# =====================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# Helper function to identify seasons from a month
def get_season_flags(month):
    """
    Returns binary flags (1 or 0) indicating which Indian season the month belongs to.
    - Summer: Feb-May (Months 2, 3, 4, 5)
    - Monsoon: Jun-Sep (Months 6, 7, 8, 9)
    - Winter: Oct-Jan (Months 10, 11, 12, 1)
    """
    is_summer = 1 if 2 <= month <= 5 else 0
    is_monsoon = 1 if 6 <= month <= 9 else 0
    is_winter = 1 if (month >= 10 or month == 1) else 0
    return is_summer, is_monsoon, is_winter

def load_data():
    """
    Loads daily usage logs and current medicine inventory from CSV files.
    - Why: Pandas is excellent at reading and manipulation of tabular CSV files.
    """
    try:
        inventory = pd.read_csv("data/medicine_inventory.csv")
        history = pd.read_csv("data/daily_usage_history.csv")
        # Ensure dates are parsed as proper date formats
        history["date"] = pd.to_datetime(history["date"])
        return inventory, history
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return None, None

def prepare_features(med_history):
    """
    Processes raw historical logs into mathematical features for scikit-learn.
    - What: Adds columns representing months, days, and seasons.
    - Why: Machine learning models only understand numbers, so we convert dates
           into numerical representations.
    """
    df = med_history.copy()
    
    # Feature 1 & 2: Extract month and day of week from date
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek
    
    # Feature 3, 4, & 5: Apply seasonal binary flags
    seasons = [get_season_flags(m) for m in df["month"]]
    df["is_summer"] = [s[0] for s in seasons]
    df["is_monsoon"] = [s[1] for s in seasons]
    df["is_winter"] = [s[2] for s in seasons]
    
    # Feature 6: Historical 7-day moving average (demand lag) to help model see local trends
    # Fill any empty values at the beginning of the rolling window with the overall average usage
    df["rolling_avg"] = df["quantity_used"].rolling(window=7, min_periods=1).mean()
    
    return df

def train_and_evaluate(medicine_name, model_type="Linear Regression"):
    """
    Trains a model specifically for the chosen medicine and prints its metrics.
    - Explainability: 
      - Train set: Past days to build the model.
      - Test set: We split 80% of data for training and 20% for testing to see
        how well our model performs on unseen data (validation).
    """
    _, history = load_data()
    if history is None:
        return None, None, "Data Error"
        
    # 1. Filter historical records for this medicine
    med_history = history[history["medicine_name"] == medicine_name].sort_values("date")
    
    if len(med_history) == 0:
        return None, None, f"Medicine '{medicine_name}' not found in history."
        
    # 2. Extract features
    processed_df = prepare_features(med_history)
    
    # 3. Define Features (X) and Target (y)
    feature_cols = ["month", "day_of_week", "is_summer", "is_monsoon", "is_winter", "rolling_avg"]
    X = processed_df[feature_cols]
    y = processed_df["quantity_used"]
    
    # 4. Train-Test Split (80% train, 20% test chronologically)
    split_idx = int(len(processed_df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # 5. Initialize the desired model
    if model_type == "Linear Regression":
        model = LinearRegression()
    else:
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        
    # 6. Fit (Train) the model
    model.fit(X_train, y_train)
    
    # 7. Evaluate Performance
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Performance summary string
    metrics_summary = f"MAE: {mae:.2f} units | R² Score: {r2:.2f}"
    
    return model, feature_cols, metrics_summary

def forecast_demand(medicine_name, model, feature_cols, days_to_forecast=30):
    """
    Forecasts demand for the next N days.
    - What: Generates future dates, extracts features, and runs model predictions.
    - How: Day by day, it predicts usage and feeds the prediction back as a lag feature
           (rolling average simulation) so the predictions remain realistic.
    """
    _, history = load_data()
    med_history = history[history["medicine_name"] == medicine_name].sort_values("date")
    processed_df = prepare_features(med_history)
    
    # Start forecasting from tomorrow
    last_date = processed_df["date"].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_to_forecast + 1)]
    
    # We maintain a list of last 7 usages to feed into 'rolling_avg' lag feature
    recent_usages = list(processed_df["quantity_used"].tail(7))
    
    forecasts = []
    
    for f_date in future_dates:
        month = f_date.month
        day_of_week = f_date.weekday()
        is_summer, is_monsoon, is_winter = get_season_flags(month)
        rolling_avg = np.mean(recent_usages)
        
        # Build standard feature input row
        input_data = pd.DataFrame([{
            "month": month,
            "day_of_week": day_of_week,
            "is_summer": is_summer,
            "is_monsoon": is_monsoon,
            "is_winter": is_winter,
            "rolling_avg": rolling_avg
        }])
        
        # Predict daily demand (returns a float, can be decimals)
        predicted_val = model.predict(input_data[feature_cols])[0]
        
        # Clean predictions: cannot sell negative items, round to whole units
        cleaned_prediction = max(0, int(round(predicted_val)))
        
        # Store prediction
        forecasts.append({
            "date": f_date.strftime("%Y-%m-%d"),
            "predicted_usage": cleaned_prediction
        })
        
        # Slide rolling window: append the predicted usage and pop oldest
        recent_usages.append(cleaned_prediction)
        recent_usages.pop(0)
        
    return pd.DataFrame(forecasts)

def predict_stockout_details(medicine_name, current_stock, model_type="Linear Regression"):
    """
    Simulates stock levels day-by-day to find the exact stock-out date.
    - What: Subtracts daily predicted demand from the current stock level.
    - Risk Colors:
      - RED (Urgent): 0-7 days left (or already out of stock)
      - YELLOW (Alert): 8-15 days left or below safe safety margin
      - GREEN (Safe): > 15 days of stock
    """
    # 1. Train model on historical logs
    model, features, metrics = train_and_evaluate(medicine_name, model_type)
    if model is None:
        return {
            "days_left": -1,
            "stockout_date": "N/A",
            "risk_level": "RED",
            "forecast_df": pd.DataFrame(),
            "metrics": "No historical data"
        }
        
    # 2. Get 30-day forecast
    forecast_df = forecast_demand(medicine_name, model, features, days_to_forecast=30)
    
    # 3. Simulate inventory drainage
    temp_stock = current_stock
    days_left = 999  # Safe default if stock lasts beyond 30 days
    stockout_date = "Safe (>30 Days)"
    
    # If stock is already empty
    if temp_stock <= 0:
        return {
            "days_left": 0,
            "stockout_date": datetime.now().strftime("%Y-%m-%d"),
            "risk_level": "RED",
            "forecast_df": forecast_df,
            "metrics": metrics
        }
        
    for index, row in forecast_df.iterrows():
        pred_usage = row["predicted_usage"]
        temp_stock -= pred_usage
        
        if temp_stock <= 0:
            days_left = index + 1  # 1-indexed
            stockout_date = row["date"]
            break
            
    # 4. Classify risk level
    if days_left <= 7:
        risk_level = "RED"
    elif days_left <= 15:
        risk_level = "YELLOW"
    else:
        risk_level = "GREEN"
        
    return {
        "days_left": days_left,
        "stockout_date": stockout_date,
        "risk_level": risk_level,
        "forecast_df": forecast_df,
        "metrics": metrics
    }

if __name__ == "__main__":
    # Test block to verify ML logic runs locally
    print("Testing ML Engine training on Paracetamol...")
    # First generate datasets if not existing
    import os
    if not os.path.exists("data/daily_usage_history.csv"):
        from data_generator import generate_datasets
        generate_datasets()
        
    inventory, _ = load_data()
    paracetamol_stock = inventory[inventory["medicine_name"] == "Paracetamol 650mg"]["current_stock"].values[0]
    
    res = predict_stockout_details("Paracetamol 650mg", paracetamol_stock, "Linear Regression")
    print(f"Paracetamol Stock: {paracetamol_stock}")
    print(f"Days left: {res['days_left']}")
    print(f"Stockout Date: {res['stockout_date']}")
    print(f"Risk level: {res['risk_level']}")
    print(f"Metrics: {res['metrics']}")
