# =====================================================================
# PROJECT: Industry-Ready Pharmacy AI Platform
# MODULE: Refactored Procurement Service (procurement_service.py)
# DESCRIPTION: Automates ordering decisions using supplier lead times,
#             safety stock buffers, and preferred supplier pricing from
#             the renamed inventory and sales_history tables.
#
# EXPLAINER FOR BEGINNERS:
# - Reorder Point (ROP): The stock level at which a new order must be placed.
#   Formula: ROP = (Daily Demand Rate * Supplier Lead Time) + Safety Stock.
# - Safety Stock: Extra inventory held as a buffer to guard against stockouts.
# =====================================================================

import pandas as pd
import numpy as np
from database.db_manager import get_connection

def calculate_reorder_points(branch_id, tenant_id):
    """
    Computes precise Reorder Points (ROP), Safety Stock (SS), and reorder suggestions
    for all medicines stocked at a specific branch.
    - Updated: Queries from inventory and sales_history tables.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Pull medicines with their preferred supplier metadata
    cursor.execute("""
        SELECT m.medicine_id, m.medicine_name, m.bilingual_name, m.category, 
               m.is_critical, m.unit_price, m.preferred_supplier_id,
               s.supplier_name, s.avg_lead_time_days, s.reliability_score
        FROM medicines m
        LEFT JOIN suppliers s ON m.preferred_supplier_id = s.supplier_id
        WHERE m.tenant_id = ?;
    """, (tenant_id,))
    medicines = cursor.fetchall()
    
    reorder_suggestions = []
    
    for med in medicines:
        med_id = med["medicine_id"]
        med_name = med["medicine_name"]
        unit_price = med["unit_price"]
        lead_time = med["avg_lead_time_days"] if med["avg_lead_time_days"] else 5.0
        
        # 2. Get active USABLE stock (from inventory table, disregarding expired batches!)
        cursor.execute("""
            SELECT SUM(quantity_stocked) 
            FROM inventory 
            WHERE medicine_id = ? AND branch_id = ? AND expiry_date > DATE('now');
        """, (med_id, branch_id))
        usable_stock_row = cursor.fetchone()
        usable_stock = usable_stock_row[0] if usable_stock_row[0] else 0
        
        # 3. Calculate historical sales statistics for this drug (from sales_history table, past 90 days)
        cursor.execute("""
            SELECT quantity_sold 
            FROM sales_history 
            WHERE medicine_id = ? AND branch_id = ? AND sale_date >= DATE('now', '-90 days');
        """, (med_id, branch_id))
        sales = [row["quantity_sold"] for row in cursor.fetchall()]
        
        if len(sales) > 5:
            avg_daily_demand = np.mean(sales)
            max_daily_demand = np.max(sales)
            std_daily_demand = np.std(sales)
        else:
            avg_daily_demand = 5.0
            max_daily_demand = 12.0
            std_daily_demand = 2.0
            
        # 4. SAFETY STOCK FORMULA:
        safety_stock = int(np.ceil(1.65 * std_daily_demand * np.sqrt(lead_time)))
        safety_stock = max(5, safety_stock)
        
        # 5. REORDER POINT FORMULA:
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
                "Marathi Label": med["bilingual_name"],
                "Is Critical?": "Yes 🚨" if med["is_critical"] == 1 else "No",
                "Category": med["category"],
                "Usable Stock": usable_stock,
                "Reorder Point (ROP)": rop,
                "Safety Stock Buffer": safety_stock,
                "Avg Daily Demand": round(avg_daily_demand, 2),
                "Supplier Name": med["supplier_name"] if med["supplier_name"] else "Local Distributor",
                "Lead Time (Days)": lead_time,
                "Recommended Qty": recommended_order_qty,
                "Unit Cost (₹)": unit_price,
                "Estimated Cost (₹)": round(recommended_order_qty * unit_price, 2),
                "Status": status
            })
            
    conn.close()
    
    if reorder_suggestions:
        df_suggest = pd.DataFrame(reorder_suggestions)
        df_suggest["sort_crit"] = df_suggest["Is Critical?"].apply(lambda x: 1 if "Yes" in x else 0)
        df_suggest = df_suggest.sort_values(by=["sort_crit", "Estimated Cost (₹)"], ascending=[False, False])
        return df_suggest.drop(columns=["sort_crit"]).to_dict("records")
        
    return []
