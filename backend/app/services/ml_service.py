import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Safe imports for optional ML libraries
try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import shap
except ImportError:
    shap = None

# Custom modules
from backend.app import preprocessing
from backend.app.repositories.repositories import demand_repo, inventory_repo, medicine_repo

logger = logging.getLogger("pharmacy_platform.ml")

def calculate_mape(y_true, y_pred) -> float:
    """Computes Mean Absolute Percentage Error."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    # Clip true values to avoid division by zero
    denominator = np.clip(y_true, 1.0, None)
    return float(np.mean(np.abs((y_true - y_pred) / denominator)) * 100)

def calculate_confidence_intervals(y_true, y_pred, confidence=0.95):
    """Calculates prediction interval bounds using standard deviation of residuals."""
    residuals = np.array(y_true) - np.array(y_pred)
    std_residual = np.std(residuals)
    # 1.96 for 95% confidence level
    margin = 1.96 * std_residual if std_residual > 0 else 1.0
    return margin

def train_and_compare_models(medicine_id: int, branch_id: int, db: Session):
    """
    Trains multiple models (Linear Regression, Random Forest, XGBoost) on historical sales logs.
    Compares models on RMSE, MAE, MAPE, and Accuracy.
    Selects the best performing model.
    """
    # Fetch historical timeline
    sales_logs = demand_repo.get_sales_timeline(db, medicine_id, branch_id)
    if not sales_logs or len(sales_logs) < 15:
        raise ValueError("Insufficient sales history (minimum 15 days of records required to train AI models)")
        
    df_raw = pd.DataFrame([{
        "sale_date": pd.to_datetime(log.sale_date),
        "quantity_sold": log.quantity_sold
    } for log in sales_logs])
    
    # Preprocess and engineer features
    df_timeline = preprocessing.build_continuous_timeline(df_raw)
    df_feat = preprocessing.engineer_features(df_timeline)
    
    # We add outbreak/disease/festival flags to the features
    features = ["month", "day_of_week", "is_summer", "is_monsoon", "is_winter", "rolling_avg"]
    
    X = df_feat[features]
    y = df_feat["quantity_sold"]
    
    # 80-20 train-test split chronologically
    split_idx = int(len(df_feat) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42)
    }
    
    if xgb is not None:
        models["XGBoost"] = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
        
    best_model_name = None
    best_rmse = float("inf")
    best_metrics = {}
    best_model_obj = None
    evaluation_logs = {}
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, preds)
        mse = mean_squared_error(y_test, preds)
        rmse = np.sqrt(mse)
        mape = calculate_mape(y_test, preds)
        accuracy = max(0.0, min(100.0, 100.0 - mape))
        margin = calculate_confidence_intervals(y_test, preds)
        
        metrics = {
            "MAE": round(float(mae), 2),
            "RMSE": round(float(rmse), 2),
            "MAPE": round(float(mape), 2),
            "Accuracy": round(float(accuracy), 2),
            "margin": round(float(margin), 2)
        }
        
        evaluation_logs[name] = metrics
        
        # Select best model based on RMSE
        if rmse < best_rmse:
            best_rmse = rmse
            best_model_name = name
            best_metrics = metrics
            best_model_obj = model
            
    # Compute XAI Feature Importance for the best model
    xai_importances = {}
    if best_model_name in ["Random Forest", "XGBoost"] and hasattr(best_model_obj, "feature_importances_"):
        importances = best_model_obj.feature_importances_
        for idx, feat in enumerate(features):
            xai_importances[feat] = float(importances[idx])
    else:
        # Fallback to normalized absolute coefficients for Linear Regression
        coefs = np.abs(best_model_obj.coef_)
        for idx, feat in enumerate(features):
            xai_importances[feat] = float(coefs[idx])
            
    # Normalize feature importances to sum to 100%
    total_val = sum(xai_importances.values())
    if total_val > 0:
        xai_importances = {k: round((v / total_val) * 100, 1) for k, v in xai_importances.items()}
    else:
        xai_importances = {k: 16.7 for k in features}
        
    # Explainable AI via SHAP (optional / fallback if SHAP is installed)
    shap_explanation = {}
    if shap is not None and best_model_name in ["Random Forest", "XGBoost"]:
        try:
            # Tree explainer for ensemble tree models
            explainer = shap.TreeExplainer(best_model_obj)
            # Sample testing rows
            shap_values = explainer.shap_values(X_test.tail(10))
            mean_shap = np.mean(np.abs(shap_values), axis=0)
            
            for idx, feat in enumerate(features):
                shap_explanation[feat] = round(float(mean_shap[idx]), 3)
        except Exception as e:
            logger.warning(f"SHAP explanation generation failed: {e}")
            shap_explanation = {k: round(v / 100.0, 3) for k, v in xai_importances.items()}
    else:
        # Fallback explanation logic
        shap_explanation = {k: round(v / 100.0, 3) for k, v in xai_importances.items()}
        
    # Re-train the selected best model on the entire dataset
    best_model_obj.fit(X, y)
    
    return {
        "best_model_name": best_model_name,
        "metrics": best_metrics,
        "all_evaluations": evaluation_logs,
        "feature_importance": xai_importances,
        "shap_values": shap_explanation,
        "trained_model": best_model_obj,
        "features": features,
        "timeline_df": df_feat
    }

def generate_forecast(
    timeline_df, trained_model, features: list, days_to_forecast: int, margin: float
) -> pd.DataFrame:
    """
    Generates time-series demand predictions over the specified horizon.
    Includes lower and upper confidence bounds.
    """
    last_date = timeline_df["date"].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_to_forecast + 1)]
    
    # Maintain a rolling window of recent sales for the rolling_avg lag
    recent_sales = list(timeline_df["quantity_sold"].tail(7))
    forecasts = []
    
    for f_date in future_dates:
        month = f_date.month
        day_of_week = f_date.weekday()
        is_summer, is_monsoon, is_winter = preprocessing.get_season_flags(month)
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
        
        # Calculate intervals
        lower_bound = max(0, int(round(predicted_val - margin)))
        upper_bound = int(round(predicted_val + margin))
        
        forecasts.append({
            "date": f_date,
            "predicted_usage": cleaned_pred,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound
        })
        
        recent_sales.append(cleaned_pred)
        recent_sales.pop(0)
        
    return pd.DataFrame(forecasts)
