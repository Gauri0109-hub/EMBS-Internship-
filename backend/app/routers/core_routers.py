import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database.session import get_db
from backend.app.schemas import schemas
from backend.app.repositories.repositories import (
    medicine_repo, supplier_repo, alert_repo, tenant_repo, branch_repo
)
from backend.app.services import auth_service, report_service, alert_service, gemini_service
from backend.app.models.models import User

router = APIRouter(prefix="", tags=["Core Platform APIs"])

# ==========================================
# MEDICINES & CATEGORIES CRUD
# ==========================================

@router.get("/medicines", response_model=List[schemas.MedicineResponse])
def list_medicines(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """Lists all cataloged medicines in the tenant group."""
    return medicine_repo.get_all_by_field(db, "tenant_id", current_user.tenant_id)

@router.post("/medicines", response_model=schemas.MedicineResponse)
def create_medicine(
    med_in: schemas.MedicineCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """Registers a new medicine formulation in the catalog."""
    return medicine_repo.create(db, {
        "tenant_id": current_user.tenant_id,
        "medicine_name": med_in.medicine_name,
        "bilingual_name": med_in.bilingual_name,
        "category_id": med_in.category_id,
        "unit_price": med_in.unit_price,
        "is_critical": med_in.is_critical,
        "preferred_supplier_id": med_in.preferred_supplier_id,
        "min_required_stock": med_in.min_required_stock
    })

@router.put("/medicines/{medicine_id}", response_model=schemas.MedicineResponse)
def update_medicine(
    medicine_id: int, 
    med_in: schemas.MedicineBase, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """Modifies properties of a registered formulation."""
    db_obj = medicine_repo.get(db, medicine_id)
    if not db_obj or db_obj.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine_repo.update(db, db_obj, med_in)

@router.delete("/medicines/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(
    medicine_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """Permanently deletes a formulation from catalog."""
    db_obj = medicine_repo.get(db, medicine_id)
    if not db_obj or db_obj.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Medicine not found")
    medicine_repo.delete(db, db_obj)
    return


# ==========================================
# SUPPLIERS CRUD
# ==========================================

@router.get("/suppliers", response_model=List[schemas.SupplierResponse])
def list_suppliers(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """Lists all suppliers registered in the tenant group."""
    return supplier_repo.get_all_by_field(db, "tenant_id", current_user.tenant_id)

@router.post("/suppliers", response_model=schemas.SupplierResponse)
def create_supplier(
    supp_in: schemas.SupplierBase, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """Registers a new supplier contact."""
    return supplier_repo.create(db, {
        "tenant_id": current_user.tenant_id,
        "supplier_name": supp_in.supplier_name,
        "contact_email": supp_in.contact_email,
        "contact_phone": supp_in.contact_phone,
        "avg_lead_time_days": supp_in.avg_lead_time_days,
        "reliability_score": supp_in.reliability_score
    })


# ==========================================
# ALERTS & RISKS API
# ==========================================

@router.get("/alerts", response_model=List[schemas.AlertResponse])
def get_alerts(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """Retrieves unresolved warnings and stock safety alerts for user's branch."""
    # Trigger dynamic database scan
    alert_service.scan_and_generate_alerts(current_user.branch_id, current_user.tenant_id, db)
    return alert_repo.get_unresolved_alerts(db, current_user.branch_id)

@router.put("/alerts/{alert_id}/resolve", response_model=schemas.AlertResponse)
def resolve_alert(
    alert_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager", "Pharmacist"]))
):
    """Marks an unresolved alert as resolved."""
    db_obj = alert_repo.get(db, alert_id)
    if not db_obj or db_obj.branch_id != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Alert record not found")
    return alert_repo.update(db, db_obj, {"is_resolved": True})


# ==========================================
# REPORTS & EXPORTS
# ==========================================

from backend.app.services.procurement_service import calculate_reorder_points

@router.get("/reports/suggestions")
def get_procurement_suggestions(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """Fetches raw procurement suggestions and ROP metrics."""
    return calculate_reorder_points(current_user.branch_id, current_user.tenant_id, db)

@router.get("/reports/pdf")
def download_pdf_report(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """Downloads procurement restocking guidelines formatted as a PDF document."""
    tenant = tenant_repo.get(db, current_user.tenant_id)
    branch = branch_repo.get(db, current_user.branch_id)
    tenant_name = tenant.company_name if tenant else "Clinic Group"
    branch_name = branch.branch_name if branch else "Branch Office"
    
    pdf_buffer = report_service.generate_pdf_report_buffer(
        current_user.branch_id, current_user.tenant_id, tenant_name, branch_name, db
    )
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=procurement_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )

@router.get("/reports/excel")
def download_excel_report(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """Downloads procurement recommendations as an Excel spreadsheet."""
    excel_buffer = report_service.generate_excel_report_buffer(current_user.branch_id, current_user.tenant_id, db)
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=procurement_orders.xlsx"}
    )

@router.get("/reports/csv")
def download_csv_report(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """Downloads procurement recommendations in raw CSV format."""
    csv_bytes = report_service.generate_csv_report_buffer(current_user.branch_id, current_user.tenant_id, db)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=procurement_orders.csv"}
    )


# ==========================================
# GEMINI AI ASSISTANT CHATBOT
# ==========================================

@router.post("/chatbot", response_model=schemas.ChatResponse)
def ask_assistant(
    query: schemas.ChatQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """Processes user query against Gemini Pro clinical chatbot model."""
    history_dict = [{"role": msg.role, "content": msg.content} for msg in query.history]
    reply = gemini_service.get_gemini_reply(
        query.message, history_dict, current_user.branch_id, current_user.tenant_id, db
    )
    return {"reply": reply}
