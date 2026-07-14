from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.repositories.repositories import alert_repo, inventory_repo, medicine_repo
from backend.app.models.models import Alert, Inventory, Medicine

def scan_and_generate_alerts(branch_id: int, tenant_id: int, db: Session):
    """
    Scans branch inventory to detect critical shortages, low stocks,
    and expiring or expired batches, and records them in the alerts table.
    """
    # 1. Fetch all medicines for this tenant
    medicines = db.query(Medicine).filter(Medicine.tenant_id == tenant_id).all()
    
    today = datetime.now().date()
    one_month_later = today + timedelta(days=30)
    
    alert_count = 0
    
    for med in medicines:
        med_id = med.medicine_id
        med_name = med.medicine_name
        min_stock = med.min_required_stock if med.min_required_stock is not None else 20
        
        # 2. Get active unexpired usable stock
        usable_stock = inventory_repo.get_usable_stock(db, med_id, branch_id)
        
        # Check for OUT OF STOCK
        if usable_stock == 0:
            msg = f"Stockout Alert: '{med_name}' is completely out of stock."
            severity = "Critical" if med.is_critical else "High"
            
            # Check if this alert already exists unresolved
            existing = db.query(Alert).filter(
                Alert.branch_id == branch_id,
                Alert.medicine_id == med_id,
                Alert.alert_type == "Out of Stock",
                Alert.is_resolved == False
            ).first()
            
            if not existing:
                alert_repo.create(db, {
                    "branch_id": branch_id,
                    "medicine_id": med_id,
                    "alert_type": "Out of Stock",
                    "message": msg,
                    "severity": severity,
                    "is_resolved": False
                })
                alert_count += 1
                
        # Check for LOW STOCK
        elif usable_stock <= min_stock:
            msg = f"Low Stock Warning: '{med_name}' is at {usable_stock} units (Safety Threshold = {min_stock})."
            severity = "High" if med.is_critical else "Medium"
            
            existing = db.query(Alert).filter(
                Alert.branch_id == branch_id,
                Alert.medicine_id == med_id,
                Alert.alert_type == "Low Stock",
                Alert.is_resolved == False
            ).first()
            
            if not existing:
                alert_repo.create(db, {
                    "branch_id": branch_id,
                    "medicine_id": med_id,
                    "alert_type": "Low Stock",
                    "message": msg,
                    "severity": severity,
                    "is_resolved": False
                })
                alert_count += 1
        
        # 3. Check for EXPIRED or EXPIRING batches in this branch
        batches = db.query(Inventory).filter(
            Inventory.medicine_id == med_id,
            Inventory.branch_id == branch_id
        ).all()
        
        for batch in batches:
            b_exp = batch.expiry_date
            
            if b_exp <= today:
                # Expired Alert
                msg = f"Expired Batch Alert: Batch '{batch.batch_number}' of '{med_name}' expired on {b_exp}."
                
                existing = db.query(Alert).filter(
                    Alert.branch_id == branch_id,
                    Alert.medicine_id == med_id,
                    Alert.alert_type == "Expired Batch",
                    Alert.message.contains(batch.batch_number),
                    Alert.is_resolved == False
                ).first()
                
                if not existing:
                    alert_repo.create(db, {
                        "branch_id": branch_id,
                        "medicine_id": med_id,
                        "alert_type": "Expired Batch",
                        "message": msg,
                        "severity": "Critical",
                        "is_resolved": False
                    })
                    alert_count += 1
                    
            elif today < b_exp <= one_month_later:
                # Expiring Soon Alert
                msg = f"Expiring Soon: Batch '{batch.batch_number}' of '{med_name}' expires on {b_exp} (within 30 days)."
                
                existing = db.query(Alert).filter(
                    Alert.branch_id == branch_id,
                    Alert.medicine_id == med_id,
                    Alert.alert_type == "Expiring Soon",
                    Alert.message.contains(batch.batch_number),
                    Alert.is_resolved == False
                ).first()
                
                if not existing:
                    alert_repo.create(db, {
                        "branch_id": branch_id,
                        "medicine_id": med_id,
                        "alert_type": "Expiring Soon",
                        "message": msg,
                        "severity": "Medium",
                        "is_resolved": False
                    })
                    alert_count += 1
                    
    return alert_count
