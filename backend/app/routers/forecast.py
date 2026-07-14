import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
from backend.app.database.session import get_db
from backend.app.schemas import schemas
from backend.app.repositories.repositories import medicine_repo, demand_repo
from backend.app.services import auth_service, ml_service
from backend.app.models.models import User
from backend.app import preprocessing

router = APIRouter(prefix="/forecast", tags=["Demand Forecasting"])

@router.get("/{medicine_id}")
def get_medicine_forecast(
    medicine_id: int,
    days_to_forecast: Optional[int] = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Runs time-series forecasting. Trains models, selects the best,
    computes confidence intervals, and generates XAI (SHAP) weights.
    """
    # Fetch medicine info
    med = medicine_repo.get(db, medicine_id)
    if not med or med.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Medicine not found")
        
    try:
        # Run ML Service auto-ML
        res_ml = ml_service.train_and_compare_models(medicine_id, current_user.branch_id, db)
        
        # Forecast daily demand
        margin = res_ml["metrics"]["margin"]
        forecast_df = ml_service.generate_forecast(
            res_ml["timeline_df"], res_ml["trained_model"], res_ml["features"], days_to_forecast, margin
        )
        
        # Format response lists
        forecast_list = []
        for _, row in forecast_df.iterrows():
            forecast_list.append({
                "date": row["date"].strftime("%Y-%m-%d"),
                "predicted_usage": int(row["predicted_usage"]),
                "lower_bound": int(row["lower_bound"]),
                "upper_bound": int(row["upper_bound"])
            })
            
        history_list = []
        # Return tail of history for timeline comparison
        hist_tail = res_ml["timeline_df"].tail(45)
        for _, row in hist_tail.iterrows():
            history_list.append({
                "date": row["date"].strftime("%Y-%m-%d"),
                "quantity_sold": int(row["quantity_sold"])
            })
            
        return {
            "medicine_name": med.medicine_name,
            "bilingual_name": med.bilingual_name,
            "best_model_name": res_ml["best_model_name"],
            "metrics": res_ml["metrics"],
            "all_evaluations": res_ml["all_evaluations"],
            "feature_importance": res_ml["feature_importance"],
            "shap_values": res_ml["shap_values"],
            "forecast": forecast_list,
            "history": history_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/import", status_code=status.HTTP_201_CREATED)
async def bulk_import_sales(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """
    Ingests daily transactions (sales/demands) spreadsheet logs,
    populating the sales history tables for ML modeling.
    """
    contents = await file.read()
    filename = file.filename
    
    try:
        if filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read spreadsheet file: {e}")
        
    try:
        # Standardize and clean using preprocessing module
        df_clean = preprocessing.validate_and_clean_sales_data(df)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
        
    records_imported = 0
    tenant_id = current_user.tenant_id
    branch_id = current_user.branch_id
    
    # 1. Cache medicines
    medicines_list = medicine_repo.get_all_by_tenant(db, tenant_id)
    medicines_cache = {m.medicine_name.lower(): m.medicine_id for m in medicines_list}
    
    for _, row in df_clean.iterrows():
        med_name = row["medicine_name"]
        sale_date = row["sale_date"]
        qty = row["quantity_sold"]
        
        # Map or add medicine
        med_lower = med_name.lower()
        if med_lower not in medicines_cache:
            med_obj = medicine_repo.create(db, {
                "tenant_id": tenant_id,
                "medicine_name": med_name,
                "category_id": None,
                "unit_price": 5.0,
                "is_critical": False,
                "min_required_stock": 20
            }, commit=False)
            db.flush()
            medicines_cache[med_lower] = med_obj.medicine_id
            med_id = med_obj.medicine_id
        else:
            med_id = medicines_cache[med_lower]
            
        # Log to demand_history table
        demand_repo.create(db, {
            "branch_id": branch_id,
            "medicine_id": med_id,
            "quantity_sold": qty,
            "sale_date": pd.to_datetime(sale_date).date()
        }, commit=False)
        records_imported += 1
        
    db.commit()
    return {"message": f"Successfully ingested {records_imported} sales transactions"}

