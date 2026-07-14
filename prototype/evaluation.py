# =====================================================================
# MODULE: Model Evaluation Metrics (evaluation.py)
# DESCRIPTION: Computes regression metrics (MAE, RMSE, R2) to validate
#             predictions and compare model accuracy.
# =====================================================================

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def calculate_metrics(y_true, y_pred):
    """
    Computes regression evaluation metrics.
    Returns MAE, RMSE, and R2.
    """
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    
    return {
        "MAE": round(float(mae), 2),
        "RMSE": round(float(rmse), 2),
        "R2": round(float(r2), 2)
    }

def format_metrics_summary(model_name, metrics):
    """Formats model evaluation metrics as a readable string."""
    return f"Best Model: {model_name} | MAE: {metrics['MAE']} | RMSE: {metrics['RMSE']} | R²: {metrics['R2']}"
