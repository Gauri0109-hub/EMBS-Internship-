# =====================================================================
# PROJECT: Industry-Ready Pharmacy AI Platform
# MODULE: Refactored ML Service (ml_service.py)
# DESCRIPTION: Queries historical transactions from the renamed sales_history table,
#             builds timelines, executes Auto-ML, and generates XAI weights.
#
# EXPLAINER FOR BEGINNERS:
# - Continuous Timeline: Sales logs might have gap dates. We fill gaps with 0 sales
#   using Pandas to keep forecasts mathematically clean.
# =====================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database.db_manager import get_connection
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def get_season_flags(month):
    """Identifies the three core Indian season flags."""
    is_summer = 1 if 2 <= month <= 5 else 0
    is_monsoon = 1 if 6 <= month <= 9 else 0
    is_winter = 1 if (month >= 10 or month == 1) else 0
    return is_summer, is_monsoon, is_winter

def fetch_continuous_timeline(medicine_id, branch_id):
    """
    Queries sales logs from sales_history table and builds a continuous date timeline.
    - Fills missing dates with 0 sales.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Updated: Query from sales_history table
    cursor.execute("""
        SELECT sale_date, SUM(quantity_sold) as quantity_sold 
        FROM sales_history
        WHERE medicine_id = ? AND branch_id = ?
        GROUP BY sale_date
        ORDER BY sale_date ASC;
    """, (medicine_id, branch_id))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return pd.DataFrame()
        
    df = pd.DataFrame([{
        "date": pd.to_datetime(row["sale_date"]),
        "quantity_sold": row["quantity_sold"]
    } for row in rows])
    
    df.set_index("date", inplace=True)
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
    df = df.reindex(full_range, fill_value=0).reset_index().rename(columns={"index": "date"})
    
    return df

def engineer_features(df):
    """Computes features (month, day, seasonal flags, and lag averages)."""
    df_feat = df.copy()
    
    df_feat["month"] = df_feat["date"].dt.month
    df_feat["day_of_week"] = df_feat["date"].dt.dayofweek
    
    seasons = [get_season_flags(m) for m in df_feat["month"]]
    df_feat["is_summer"] = [s[0] for s in seasons]
    df_feat["is_monsoon"] = [s[1] for s in seasons]
    df_feat["is_winter"] = [s[2] for s in seasons]
    
    df_feat["rolling_avg"] = df_feat["quantity_sold"].rolling(window=7, min_periods=1).mean()
    return df_feat

def train_ensemble_and_select_best(medicine_id, branch_id):
    """
    Trains Linear Regression, Random Forest, and Gradient Boosting.
    - Evaluates performance metrics on test validation split (80-20).
    - Automatically selects and returns the best model based on RMSE.
    """
    df_raw = fetch_continuous_timeline(medicine_id, branch_id)
    if df_raw.empty or len(df_raw) < 15:
        return None, None, "Insufficient data (minimum 15 sales records needed)"
        
    df_feat = engineer_features(df_raw)
    
    features = ["month", "day_of_week", "is_summer", "is_monsoon", "is_winter", "rolling_avg"]
    X = df_feat[features]
    y = df_feat["quantity_sold"]
    
    split_idx = int(len(df_feat) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=50, random_state=42),
        "Gradient Boosting (Ensemble)": GradientBoostingRegressor(n_estimators=50, random_state=42)
    }
    
    evaluation_results = {}
    best_model_name = None
    best_rmse = float("inf")
    trained_models = {}
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        trained_models[name] = model
        
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        mse = mean_squared_error(y_test, preds)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, preds)
        
        evaluation_results[name] = {
            "MAE": round(float(mae), 3),
            "RMSE": round(float(rmse), 3),
            "R2": round(float(r2), 3),
            "model": model
        }
        
        if rmse < best_rmse:
            best_rmse = rmse
            best_model_name = name
            
    best_model_info = evaluation_results[best_model_name]
    
    best_model = best_model_info["model"]
    xai_dict = {}
    
    if best_model_name == "Linear Regression":
        weights = best_model.coef_
        for idx, feat in enumerate(features):
            xai_dict[feat] = float(weights[idx])
    else:
        importances = best_model.feature_importances_
        for idx, feat in enumerate(features):
            xai_dict[feat] = float(importances[idx])
            
    total_val = sum(abs(v) for v in xai_dict.values())
    if total_val > 0:
        xai_dict = {k: round((abs(v) / total_val) * 100, 1) for k, v in xai_dict.items()}
        
    return {
        "best_model_name": best_model_name,
        "metrics": f"{best_model_name} | RMSE: {best_model_info['RMSE']} | MAE: {best_model_info['MAE']} | R²: {best_model_info['R2']}",
        "raw_metrics": best_model_info,
        "xai": xai_dict,
        "trained_model": best_model,
        "features": features,
        "timeline_df": df_feat
    }, None, "Success"

def generate_forecast_30_days(medicine_id, branch_id, trained_model, features, timeline_df):
    """
    Generates 30 days daily forecast using trained model and recent lag averages.
    """
    last_date = timeline_df["date"].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
    
    recent_sales = list(timeline_df["quantity_sold"].tail(7))
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
            "date": f_date.strftime("%Y-%m-%d"),
            "predicted_usage": cleaned_pred
        })
        
        recent_sales.append(cleaned_pred)
        recent_sales.pop(0)
        
    return pd.DataFrame(forecasts)
