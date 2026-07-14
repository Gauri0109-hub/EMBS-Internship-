import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database.session import get_db
from backend.app.schemas import schemas
from backend.app.repositories.repositories import inventory_repo, medicine_repo, supplier_repo
from backend.app.services import auth_service
from backend.app.models.models import User
from backend.app import preprocessing

router = APIRouter(prefix="/inventory", tags=["Inventory Management"])

@router.get("", response_model=List[schemas.InventoryResponse])
def get_inventory(
    db: Session = Depends(get_db),
    medicine_id: Optional[int] = None,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Fetches inventory items for the user's branch."""
    if medicine_id:
        return inventory_repo.get_batches(db, medicine_id, current_user.branch_id)
    return inventory_repo.get_all_by_field(db, "branch_id", current_user.branch_id)

@router.post("", response_model=schemas.InventoryResponse)
def log_incoming_batch(
    inventory_in: schemas.InventoryBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager", "Pharmacist"]))
):
    """Logs a new incoming medicine batch into inventory."""
    return inventory_repo.create(db, {
        "medicine_id": inventory_in.medicine_id,
        "branch_id": current_user.branch_id,
        "batch_number": inventory_in.batch_number,
        "quantity_stocked": inventory_in.quantity_stocked,
        "expiry_date": inventory_in.expiry_date
    })

@router.delete("/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """Removes an inventory batch from stock."""
    db_obj = inventory_repo.get(db, inventory_id)
    if not db_obj or db_obj.branch_id != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Inventory batch not found")
    inventory_repo.delete(db, db_obj)
    return

@router.post("/import", status_code=status.HTTP_201_CREATED)
async def bulk_import_inventory(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """
    Ingests and cleanses bulk inventory CSV or Excel spreadsheets,
    inserting new medicines, suppliers, and batches into relational tables.
    """
    contents = await file.read()
    filename = file.filename
    
    try:
        import pandas as pd
        if filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read spreadsheet file: {e}")
        
    try:
        # Standardize and clean using preprocessing module
        df_clean = preprocessing.validate_and_clean_inventory_data(df)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
        
    records_imported = 0
    tenant_id = current_user.tenant_id
    branch_id = current_user.branch_id
    
    # 1. Fetch current suppliers and medicines to avoid duplicates
    suppliers_list = supplier_repo.get_all_by_field(db, "tenant_id", tenant_id)
    suppliers_cache = {s.supplier_name.lower(): s.supplier_id for s in suppliers_list}
    
    medicines_list = medicine_repo.get_all_by_tenant(db, tenant_id)
    medicines_cache = {m.medicine_name.lower(): m.medicine_id for m in medicines_list}
    
    for _, row in df_clean.iterrows():
        med_name = row["medicine_name"]
        supp_name = row["supplier_name"]
        category = row["category"]
        qty = row["current_stock"]
        exp = row["expiry_date"]
        is_crit = True if row["is_critical"] == "Yes" else False
        
        # Map or add supplier
        supp_lower = supp_name.lower()
        if supp_lower not in suppliers_cache:
            supp_obj = supplier_repo.create(db, {
                "tenant_id": tenant_id,
                "supplier_name": supp_name,
                "avg_lead_time_days": 5.0,
                "reliability_score": 95.0
            }, commit=False)
            db.flush()
            suppliers_cache[supp_lower] = supp_obj.supplier_id
            supp_id = supp_obj.supplier_id
        else:
            supp_id = suppliers_cache[supp_lower]
            
        # Map or add medicine
        med_lower = med_name.lower()
        if med_lower not in medicines_cache:
            med_obj = medicine_repo.create(db, {
                "tenant_id": tenant_id,
                "medicine_name": med_name,
                "category_id": None, # Unassigned category
                "unit_price": 5.0,
                "is_critical": is_crit,
                "preferred_supplier_id": supp_id,
                "min_required_stock": 20
            }, commit=False)
            db.flush()
            medicines_cache[med_lower] = med_obj.medicine_id
            med_id = med_obj.medicine_id
        else:
            med_id = medicines_cache[med_lower]
            
        # Insert batch into inventory
        from datetime import datetime
        batch_num = f"IMP-{datetime.now().strftime('%m%d%H%M')}-{records_imported:03d}"
        inventory_repo.create(db, {
            "medicine_id": med_id,
            "branch_id": branch_id,
            "batch_number": batch_num,
            "quantity_stocked": qty,
            "expiry_date": pd.to_datetime(exp).date()
        }, commit=False)
        records_imported += 1
        
    db.commit()
    return {"message": f"Successfully ingested {records_imported} inventory records"}

