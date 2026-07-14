# =====================================================================
# MODULE: ML Model Training & Prediction (prediction.py)
# DESCRIPTION: Trains Linear Regression and Random Forest Regressors,
#             compares their RMSE metrics, selects the best-performing model,
#             forecasts future daily demand, and determines stock risk tiers.
# =====================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from preprocessing import engineer_features, get_season_flags
from evaluation import calculate_metrics

def train_and_compare_models(timeline_df):
    """
    Trains Linear Regression and Random Forest Regressor models on timeline_df.
    Compares their RMSE on 80-20 validation split and selects the best model.
    Returns:
        model: Trained best model (refit on all data)
        model_name: Selected model's name
        metrics: Dictionary of best model evaluation metrics (MAE, RMSE, R2)
        features: List of features used
        xai_importances: Dictionary of feature weights/importances
    """
    if timeline_df.empty or len(timeline_df) < 15:
        raise ValueError("Insufficient sales records (minimum 15 records required to train ML model)")
        
    df_feat = engineer_features(timeline_df)
    
    features = ["month", "day_of_week", "is_summer", "is_monsoon", "is_winter", "rolling_avg"]
    X = df_feat[features]
    y = df_feat["quantity_sold"]
    
    # Train-test split (80% train, 20% validation chronologically)
    split_idx = int(len(df_feat) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # Define models
    lr_model = LinearRegression()
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    # Train and evaluate Linear Regression
    lr_model.fit(X_train, y_train)
    lr_preds = lr_model.predict(X_test)
    lr_metrics = calculate_metrics(y_test, lr_preds)
    
    # Train and evaluate Random Forest
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_metrics = calculate_metrics(y_test, rf_preds)
    
    # Compare RMSE (lower is better)
    if rf_metrics["RMSE"] <= lr_metrics["RMSE"]:
        best_model_name = "Random Forest"
        best_model = RandomForestRegressor(n_estimators=100, random_state=42)
        best_metrics = rf_metrics
        # Feature importances for XAI
        importances = rf_model.feature_importances_
        xai_importances = {feat: float(importances[idx]) for idx, feat in enumerate(features)}
    else:
        best_model_name = "Linear Regression"
        best_model = LinearRegression()
        best_metrics = lr_metrics
        # Coefficients for XAI (take absolute values)
        coefs = np.abs(lr_model.coef_)
        xai_importances = {feat: float(coefs[idx]) for idx, feat in enumerate(features)}
        
    # Normalize XAI importances to sum to 100%
    total_val = sum(xai_importances.values())
    if total_val > 0:
        xai_importances = {k: round((v / total_val) * 100, 1) for k, v in xai_importances.items()}
    else:
        xai_importances = {k: 16.7 for k in features} # Equal weight if all zero
        
    # Refit selected model on full dataset
    best_model.fit(X, y)
    
    return best_model, best_model_name, best_metrics, features, xai_importances

def forecast_demand(timeline_df, trained_model, features, days_to_forecast=30):
    """
    Generates forecast for the next N days.
    Feeds predicted usage back as lags dynamically.
    """
    df_feat = engineer_features(timeline_df)
    last_date = df_feat["date"].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_to_forecast + 1)]
    
    # Maintain rolling lag list of last 7 usages
    recent_sales = list(df_feat["quantity_sold"].tail(7))
    forecasts = []
    
    for f_date in future_dates:
        month = f_date.month
        day_of_week = f_date.weekday()
        is_summer, is_monsoon, is_winter = get_season_flags(month)
        rolling_avg = np.mean(recent_sales)
        
        input_row = pd.DataFrame([{
            "month": month,
            "day_of_week": day_of_week,
            "is_summer": is_summer,
            "is_monsoon": is_monsoon,
            "is_winter": is_winter,
            "rolling_avg": rolling_avg
        }])
        
        predicted_val = trained_model.predict(input_row[features])[0]
        cleaned_pred = max(0, int(round(predicted_val)))
        
        forecasts.append({
            "date": f_date,
            "predicted_usage": cleaned_pred
        })
        
        recent_sales.append(cleaned_pred)
        recent_sales.pop(0)
        
    return pd.DataFrame(forecasts)

def simulate_stockout_and_risk(current_stock, min_required_stock, forecast_df, forecast_days):
    """
    Simulates inventory depletion day-by-day.
    Classifies risk levels and recommended actions based on predicted demand and ROP.
    Returns:
        predicted_demand: Total units demanded over the forecast horizon
        days_left: Number of days stock lasts
        stockout_date: Date stockout happens, or "Safe"
        risk_level: Red, Orange, Yellow, Green
        recommended_action: String description of what action to take
    """
    # Slice forecast_df to the desired forecast horizon
    sliced_forecast = forecast_df.head(forecast_days).copy()
    predicted_demand = int(sliced_forecast["predicted_usage"].sum())
    
    temp_stock = current_stock
    days_left = 999
    stockout_date = "Safe (>30 Days)"
    
    if temp_stock <= 0:
        days_left = 0
        stockout_date = datetime.now().strftime("%Y-%m-%d")
    else:
        for idx, row in forecast_df.iterrows():
            temp_stock -= row["predicted_usage"]
            if temp_stock <= 0:
                days_left = idx + 1
                stockout_date = row["date"].strftime("%Y-%m-%d")
                break
                
    # Classify risk and determine recommended actions
    if days_left <= 7:
        risk_level = "Red"
        recommended_action = "Restock immediately! Stock is critical."
    elif days_left <= 14:
        risk_level = "Orange"
        recommended_action = "High Risk. Place order within 48 hours."
    elif days_left <= 30 or current_stock < min_required_stock:
        risk_level = "Yellow"
        recommended_action = "Medium Warning. Monitor stock and plan next reorder."
    else:
        risk_level = "Green"
        recommended_action = "Safe. Usable stock is sufficient."
        
    return {
        "predicted_demand": predicted_demand,
        "days_left": days_left,
        "stockout_date": stockout_date,
        "risk_level": risk_level,
        "recommended_action": recommended_action
    }
