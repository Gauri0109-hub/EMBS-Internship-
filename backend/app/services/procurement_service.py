import numpy as np
from sqlalchemy.orm import Session
from datetime import date, timedelta
from backend.app.database.session import SessionLocal
from backend.app.models.models import Medicine, Inventory, DemandHistory, Supplier
from backend.app.repositories.repositories import inventory_repo

def calculate_reorder_points(branch_id: int, tenant_id: int, db: Session = None):
    """
    Computes precise Reorder Points (ROP), Safety Stock (SS), and reorder suggestions
    using SQLAlchemy session.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True
        
    try:
        # 1. Pull medicines with preferred supplier
        medicines = db.query(Medicine).filter(Medicine.tenant_id == tenant_id).all()
        
        reorder_suggestions = []
        today = date.today()
        ninety_days_ago = today - timedelta(days=90)
        
        for med in medicines:
            med_id = med.medicine_id
            med_name = med.medicine_name
            unit_price = med.unit_price if med.unit_price else 5.0
            
            # Fetch preferred supplier lead time
            lead_time = 5.0
            supplier_name = "Local Distributor"
            if med.supplier:
                lead_time = med.supplier.avg_lead_time_days if med.supplier.avg_lead_time_days else 5.0
                supplier_name = med.supplier.supplier_name
                
            # 2. Get active USABLE stock
            usable_stock = inventory_repo.get_usable_stock(db, med_id, branch_id)
            
            # 3. Calculate historical sales statistics past 90 days
            sales_records = db.query(DemandHistory.quantity_sold).filter(
                DemandHistory.medicine_id == med_id,
                DemandHistory.branch_id == branch_id,
                DemandHistory.sale_date >= ninety_days_ago
            ).all()
            
            sales = [row[0] for row in sales_records]
            
            if len(sales) > 5:
                avg_daily_demand = np.mean(sales)
                max_daily_demand = np.max(sales)
                std_daily_demand = np.std(sales)
            else:
                avg_daily_demand = 5.0
                max_daily_demand = 12.0
                std_daily_demand = 2.0
                
            # 4. Safety Stock Formula
            safety_stock = int(np.ceil(1.65 * std_daily_demand * np.sqrt(lead_time)))
            safety_stock = max(5, safety_stock)
            
            # 5. Reorder Point Formula
            rop = int(np.ceil(avg_daily_demand * lead_time)) + safety_stock
            
            # 6. Check if current stock triggers reorder
            status = "🟢 Safe"
            reorder_needed = 0
            recommended_order_qty = 0
            
            if usable_stock == 0:
                status = "🔴 OUT OF STOCK"
                reorder_needed = 1
                recommended_order_qty = int(np.ceil(avg_daily_demand * 30)) + safety_stock
            elif usable_stock <= rop:
                status = "🟡 Low Stock (Reorder)"
                reorder_needed = 1
                recommended_order_qty = int(np.ceil(avg_daily_demand * 30)) + safety_stock - usable_stock
                
            if reorder_needed:
                reorder_suggestions.append({
                    "Medicine ID": f"MED{med_id:03d}",
                    "medicine_id_raw": med_id,
                    "Medicine Name": med_name,
                    "Marathi Label": med.bilingual_name,
                    "Is Critical?": "Yes 🚨" if med.is_critical else "No",
                    "Category": med.category.category_name if med.category else "General",
                    "Usable Stock": usable_stock,
                    "Reorder Point (ROP)": rop,
                    "Safety Stock Buffer": safety_stock,
                    "Avg Daily Demand": round(avg_daily_demand, 2),
                    "Supplier Name": supplier_name,
                    "Lead Time (Days)": lead_time,
                    "Recommended Qty": recommended_order_qty,
                    "Unit Cost (₹)": unit_price,
                    "Estimated Cost (₹)": round(recommended_order_qty * unit_price, 2),
                    "Status": status
                })
                
        if reorder_suggestions:
            reorder_suggestions.sort(key=lambda x: (1 if "Yes" in x["Is Critical?"] else 0, x["Estimated Cost (₹)"]), reverse=True)
            return reorder_suggestions
            
        return []
        
    finally:
        if own_session:
            db.close()
