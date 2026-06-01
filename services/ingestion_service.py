# =====================================================================
# PROJECT: Industry-Ready Pharmacy AI Platform
# MODULE: Refactored Data Ingestion Pipeline (ingestion_service.py)
# DESCRIPTION: Uploads, validates, cleans, and imports CSV and Excel (.xlsx)
#             datasets into the renamed 10 database tables (inventory,
#             sales_history, and uploads).
#
# EXPLAINER FOR BEGINNERS:
# - Data Cleansing: Automatically correcting or removing faulty records
#   (e.g., negative inventory levels, empty medicine names, or garbled dates)
#   so the system doesn't crash during analysis or training.
# - Schema Validation: Confirming that the uploaded file has all required
#   columns before allowing it into the database.
# =====================================================================

import pandas as pd
import numpy as np
from datetime import datetime
from database.db_manager import get_connection

def parse_date_safely(date_val):
    """
    Attempts to parse date strings using multiple standard formats.
    - Returns string in 'YYYY-MM-DD' format if successful.
    - Returns None if parsing fails.
    """
    if pd.isna(date_val):
        return None
        
    date_str = str(date_val).strip()
    
    # Try parsing Excel float timestamp first
    try:
        if date_str.replace('.', '', 1).isdigit():
            return pd.to_datetime(float(date_str), unit='D', origin='1899-12-30').strftime("%Y-%m-%d")
    except:
        pass
        
    # List of common formats to try
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y",
        "%Y/%m/%d", "%d-%b-%Y", "%d %B %Y", "%Y-%m-%d %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    # Fall back to pandas parser
    try:
        return pd.to_datetime(date_str).strftime("%Y-%m-%d")
    except:
        return None

def validate_inventory_upload(file_obj, filename):
    """
    Validates and cleanses inventory CSV/Excel files.
    - Checks required columns: 'Medicine Name', 'Current Stock', 'Expiry Date'
    - Cleans negative stock levels (replaces with 0).
    - Validates expiry date strings.
    """
    results = {
        "status": "success",
        "errors": [],
        "warnings": [],
        "preview": None,
        "records_count": 0,
        "cleansed_df": None
    }
    
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_obj)
        else:
            df = pd.read_csv(file_obj)
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Failed to read file: {e}")
        return results
        
    # Check Column Schema
    col_mapping = {
        "Medicine Name": ["medicine_name", "medicine name", "name", "Medicine Name"],
        "Current Stock": ["current_stock", "current stock", "stock", "quantity", "Quantity", "Current Stock"],
        "Expiry Date": ["expiry_date", "expiry date", "expiry", "Expiry Date", "Expiry"]
    }
    
    found_cols = {}
    for standard_col, variants in col_mapping.items():
        for var in variants:
            if var in df.columns:
                found_cols[standard_col] = var
                break
                
    missing_cols = [col for col in col_mapping.keys() if col not in found_cols]
    if missing_cols:
        results["status"] = "error"
        results["errors"].append(f"Missing required columns: {', '.join(missing_cols)}. Check templates!")
        return results
        
    # Standardize
    df = df.rename(columns={
        found_cols["Medicine Name"]: "medicine_name",
        found_cols["Current Stock"]: "current_stock",
        found_cols["Expiry Date"]: "expiry_date"
    })
    
    # Optional columns
    opt_mapping = {
        "category": ["category", "Category"],
        "supplier_name": ["supplier", "Supplier", "supplier_name"],
        "is_critical": ["is_critical", "critical", "Critical Medicine Flag", "is critical"]
    }
    for standard_col, variants in opt_mapping.items():
        for var in variants:
            if var in df.columns:
                df = df.rename(columns={var: standard_col})
                break
                
    cleansed_rows = []
    for idx, row in df.iterrows():
        med_name = str(row["medicine_name"]).strip() if not pd.isna(row["medicine_name"]) else ""
        if not med_name:
            results["warnings"].append(f"Row {idx+2}: Empty medicine name. Row skipped.")
            continue
            
        try:
            stock_qty = int(float(row["current_stock"]))
            if stock_qty < 0:
                results["warnings"].append(f"Row {idx+2} ('{med_name}'): Negative stock level ({stock_qty}) found. Reset to 0.")
                stock_qty = 0
        except (ValueError, TypeError):
            results["warnings"].append(f"Row {idx+2} ('{med_name}'): Malformed stock level. Reset to 0.")
            stock_qty = 0
            
        parsed_date = parse_date_safely(row["expiry_date"])
        if not parsed_date:
            results["warnings"].append(f"Row {idx+2} ('{med_name}'): Invalid expiry date format ('{row['expiry_date']}'). Defaulting to 1 year from now.")
            parsed_date = (datetime.now() + pd.Timedelta(days=365)).strftime("%Y-%m-%d")
            
        category = str(row.get("category", "Uncategorized")).strip()
        supplier = str(row.get("supplier_name", "Local Vendor")).strip()
        is_crit = str(row.get("is_critical", "No")).strip()
        is_crit = "Yes" if is_crit.lower() in ["yes", "y", "1", "true"] else "No"
        
        cleansed_rows.append({
            "medicine_name": med_name,
            "current_stock": stock_qty,
            "expiry_date": parsed_date,
            "category": category,
            "supplier_name": supplier,
            "is_critical": is_crit
        })
        
    cleansed_df = pd.DataFrame(cleansed_rows)
    results["records_count"] = len(cleansed_df)
    results["preview"] = cleansed_df.head(10)
    results["cleansed_df"] = cleansed_df
    
    return results

def validate_sales_upload(file_obj, filename):
    """
    Validates and cleanses historical sales CSV/Excel files.
    - Checks required columns: 'Date', 'Medicine Name', 'Quantity Sold'
    """
    results = {
        "status": "success",
        "errors": [],
        "warnings": [],
        "preview": None,
        "records_count": 0,
        "cleansed_df": None
    }
    
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_obj)
        else:
            df = pd.read_csv(file_obj)
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Failed to read file: {e}")
        return results
        
    # Check Column Schema
    col_mapping = {
        "Date": ["date", "Date", "sale_date", "sale date", "Day"],
        "Medicine Name": ["medicine_name", "medicine name", "name", "Medicine Name"],
        "Quantity Sold": ["quantity_sold", "quantity sold", "quantity", "Quantity Sold", "Quantity", "qty", "Qty"]
    }
    
    found_cols = {}
    for standard_col, variants in col_mapping.items():
        for var in variants:
            if var in df.columns:
                found_cols[standard_col] = var
                break
                
    missing_cols = [col for col in col_mapping.keys() if col not in found_cols]
    if missing_cols:
        results["status"] = "error"
        results["errors"].append(f"Missing required columns: {', '.join(missing_cols)}. Check templates!")
        return results
        
    # Standardize
    df = df.rename(columns={
        found_cols["Date"]: "sale_date",
        found_cols["Medicine Name"]: "medicine_name",
        found_cols["Quantity Sold"]: "quantity_sold"
    })
    
    cleansed_rows = []
    for idx, row in df.iterrows():
        med_name = str(row["medicine_name"]).strip() if not pd.isna(row["medicine_name"]) else ""
        if not med_name:
            results["warnings"].append(f"Row {idx+2}: Empty medicine name. Row skipped.")
            continue
            
        try:
            qty_sold = int(float(row["quantity_sold"]))
            if qty_sold <= 0:
                results["warnings"].append(f"Row {idx+2} ('{med_name}'): Non-positive quantity sold ({qty_sold}). Row skipped.")
                continue
        except (ValueError, TypeError):
            results["warnings"].append(f"Row {idx+2} ('{med_name}'): Malformed sale quantity. Row skipped.")
            continue
            
        parsed_date = parse_date_safely(row["sale_date"])
        if not parsed_date:
            results["warnings"].append(f"Row {idx+2} ('{med_name}'): Invalid date format ('{row['sale_date']}'). Row skipped.")
            continue
            
        cleansed_rows.append({
            "sale_date": parsed_date,
            "medicine_name": med_name,
            "quantity_sold": qty_sold
        })
        
    cleansed_df = pd.DataFrame(cleansed_rows)
    results["records_count"] = len(cleansed_df)
    results["preview"] = cleansed_df.head(10)
    results["cleansed_df"] = cleansed_df
    
    return results

def import_inventory_to_db(cleansed_df, tenant_id, branch_id, filename, username):
    """
    Inserts validated inventory records into the SQLite database.
    - Updated: Inserts batches into 'inventory' table, logs into 'uploads' table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # 1. Fetch current suppliers to avoid duplicates
        cursor.execute("SELECT supplier_id, supplier_name FROM suppliers WHERE tenant_id = ?;", (tenant_id,))
        suppliers_cache = {row["supplier_name"].lower(): row["supplier_id"] for row in cursor.fetchall()}
        
        # 2. Fetch current medicines to avoid duplicates
        cursor.execute("SELECT medicine_id, medicine_name FROM medicines WHERE tenant_id = ?;", (tenant_id,))
        medicines_cache = {row["medicine_name"].lower(): row["medicine_id"] for row in cursor.fetchall()}
        
        records_imported = 0
        
        for _, row in cleansed_df.iterrows():
            med_name = row["medicine_name"]
            supp_name = row["supplier_name"]
            category = row["category"]
            qty = row["current_stock"]
            exp = row["expiry_date"]
            is_crit = 1 if row["is_critical"] == "Yes" else 0
            
            # Map or add supplier
            supp_lower = supp_name.lower()
            if supp_lower not in suppliers_cache:
                cursor.execute("""
                    INSERT INTO suppliers (tenant_id, supplier_name, avg_lead_time_days, reliability_score)
                    VALUES (?, ?, 5.0, 95.0);
                """, (tenant_id, supp_name))
                supp_id = cursor.lastrowid
                suppliers_cache[supp_lower] = supp_id
            else:
                supp_id = suppliers_cache[supp_lower]
                
            # Map or add medicine
            med_lower = med_name.lower()
            if med_lower not in medicines_cache:
                cursor.execute("""
                    INSERT INTO medicines (tenant_id, medicine_name, category, is_critical, unit_price, preferred_supplier_id)
                    VALUES (?, ?, ?, ?, 5.0, ?);
                """, (tenant_id, med_name, category, is_crit, supp_id))
                med_id = cursor.lastrowid
                medicines_cache[med_lower] = med_id
            else:
                med_id = medicines_cache[med_lower]
                
            # Insert into inventory table (Renamed from medicine_batches)
            batch_num = f"IMP-{datetime.now().strftime('%m%d%H%M')}-{idx_number(records_imported)}"
            cursor.execute("""
                INSERT INTO inventory (medicine_id, branch_id, batch_number, quantity_stocked, expiry_date)
                VALUES (?, ?, ?, ?, ?);
            """, (med_id, branch_id, batch_num, qty, exp))
            
            records_imported += 1
            
        # Log the import history in uploads table (Renamed from import_logs)
        cursor.execute("""
            INSERT INTO uploads (tenant_id, branch_id, filename, records_imported, uploaded_by)
            VALUES (?, ?, ?, ?, ?);
        """, (tenant_id, branch_id, filename, records_imported, username))
        
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        return True, records_imported
        
    except Exception as e:
        conn.rollback()
        print(f"Error during inventory bulk import: {e}")
        return False, 0
    finally:
        conn.close()

def import_sales_to_db(cleansed_df, tenant_id, branch_id, filename, username):
    """
    Inserts validated historical demand records into the SQLite database.
    - Updated: Inserts sales logs to 'sales_history' table, uploads log to 'uploads' table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # Cache medicines
        cursor.execute("SELECT medicine_id, medicine_name FROM medicines WHERE tenant_id = ?;", (tenant_id,))
        medicines_cache = {row["medicine_name"].lower(): row["medicine_id"] for row in cursor.fetchall()}
        
        records_imported = 0
        
        for _, row in cleansed_df.iterrows():
            med_name = row["medicine_name"]
            sale_date = row["sale_date"]
            qty = row["quantity_sold"]
            
            med_lower = med_name.lower()
            if med_lower not in medicines_cache:
                cursor.execute("""
                    INSERT INTO medicines (tenant_id, medicine_name, category, is_critical, unit_price)
                    VALUES (?, ?, 'Uncategorized', 0, 5.0);
                """, (tenant_id, med_name))
                med_id = cursor.lastrowid
                medicines_cache[med_lower] = med_id
            else:
                med_id = medicines_cache[med_lower]
                
            # Insert to sales_history table (Renamed from sales_transactions)
            cursor.execute("""
                INSERT INTO sales_history (branch_id, medicine_id, quantity_sold, sale_date)
                VALUES (?, ?, ?, ?);
            """, (branch_id, med_id, qty, sale_date))
            
            records_imported += 1
            
        # Log to uploads table (Renamed from import_logs)
        cursor.execute("""
            INSERT INTO uploads (tenant_id, branch_id, filename, records_imported, uploaded_by)
            VALUES (?, ?, ?, ?, ?);
        """, (tenant_id, branch_id, filename, records_imported, username))
        
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        return True, records_imported
        
    except Exception as e:
        conn.rollback()
        print(f"Error during sales bulk import: {e}")
        return False, 0
    finally:
        conn.close()

def idx_number(num):
    """Helper to pad index numbering."""
    return f"{num:03d}"
