# =====================================================================
# PROJECT: Industry-Ready Pharmacy AI Platform
# MODULE: Refactored ML Service (ml_service.py)
# DESCRIPTION: Queries historical transactions from the database,
#             delegates model training to prediction.py, and manages forecasting.
# =====================================================================

import pandas as pd
import numpy as np
from database.db_manager import get_connection
import preprocessing
import prediction
import evaluation
import utils

def get_season_flags(month):
    return preprocessing.get_season_flags(month)

def fetch_continuous_timeline(medicine_id, branch_id):
    return utils.get_sales_timeline_db(medicine_id, branch_id)

def engineer_features(df):
    return preprocessing.engineer_features(df)

def train_ensemble_and_select_best(medicine_id, branch_id):
    """
    Trains Linear Regression and Random Forest Regressor models on historical data.
    Automatically selects the best model based on RMSE metric.
    """
    timeline_df = utils.get_sales_timeline_db(medicine_id, branch_id)
    if timeline_df.empty or len(timeline_df) < 15:
        return None, None, "Insufficient data (minimum 15 sales records needed)"
        
    try:
        model, model_name, metrics, features, xai_importances = prediction.train_and_compare_models(timeline_df)
        
        # Fit metrics display
        metrics_summary = f"{model_name} | RMSE: {metrics['RMSE']} | MAE: {metrics['MAE']} | R²: {metrics['R2']}"
        
        return {
            "best_model_name": model_name,
            "metrics": metrics_summary,
            "raw_metrics": metrics,
            "xai": xai_importances,
            "trained_model": model,
            "features": features,
            "timeline_df": timeline_df
        }, None, "Success"
    except Exception as e:
        return None, str(e), f"Error training models: {e}"

def generate_forecast_30_days(medicine_id, branch_id, trained_model, features, timeline_df):
    """
    Generates a 30-day forecast for daily usage.
    """
    try:
        forecast_df = prediction.forecast_demand(timeline_df, trained_model, features, days_to_forecast=30)
        # Format date column as string for downstream UI components
        forecast_df["date"] = forecast_df["date"].dt.strftime("%Y-%m-%d")
        return forecast_df
    except Exception as e:
        print(f"Error forecasting: {e}")
        return pd.DataFrame()
