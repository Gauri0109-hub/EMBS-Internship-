# =====================================================================
# PROJECT: Enterprise Pharmacy AI Platform
# MODULE: Database Manager & Migrator (database/db_manager.py)
# DESCRIPTION: Manages SQLite relational databases, initializes the 10
#             core tables, executes automatic schema migrations, and populates
#             default tenant, supplier, medicine, batch, and transaction records.
#
# EXPLAINER FOR BEGINNERS:
# - Schema Migrations: Code that checks if database tables have changed (like adding
#   a missing column) and upgrades the database file without losing user data!
# - SQLite Relational Schema: Using primary keys and foreign keys to link
#   tables together, representing a real-world multi-tenant business database.
# =====================================================================

import sqlite3
import os
import hashlib
import numpy as np
from datetime import datetime, timedelta

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "pharmacy_platform.db")

# Create data directory if missing
os.makedirs(DB_DIR, exist_ok=True)

def hash_password(password: str) -> str:
    """Securely hashes passwords using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_connection():
    """Returns a connection to the SQLite database with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name like dictionary
    conn.execute("PRAGMA foreign_keys = ON;") # Enforce foreign key constraints
    return conn

def migrate_database():
    """
    Checks the existing database schema and applies migrations safely:
    - Adds missing columns (e.g. min_required_stock).
    - Upgrades older tables to the new 10-table structure without losing data.
    """
    if not os.path.exists(DB_PATH):
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check medicines table columns
        cursor.execute("PRAGMA table_info(medicines);")
        columns = [row["name"] for row in cursor.fetchall()]
        
        if columns and "min_required_stock" not in columns:
            print("Migrating: Adding min_required_stock to medicines table...")
            cursor.execute("ALTER TABLE medicines ADD COLUMN min_required_stock INTEGER DEFAULT 20;")
            conn.commit()
            print("Migration successful: added min_required_stock.")
            
        # Handle rename migrations from old tables to the new 10 tables structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        
        # Rename medicine_batches to inventory
        if "medicine_batches" in tables and "inventory" not in tables:
            print("Migrating: Renaming medicine_batches to inventory...")
            cursor.execute("ALTER TABLE medicine_batches RENAME TO inventory;")
            cursor.execute("ALTER TABLE inventory RENAME COLUMN batch_id TO inventory_id;")
            conn.commit()
            
        # Rename sales_transactions to sales_history
        if "sales_transactions" in tables and "sales_history" not in tables:
            print("Migrating: Renaming sales_transactions to sales_history...")
            cursor.execute("ALTER TABLE sales_transactions RENAME TO sales_history;")
            cursor.execute("ALTER TABLE sales_history RENAME COLUMN transaction_id TO sale_id;")
            conn.commit()
            
        # Rename import_logs to uploads
        if "import_logs" in tables and "uploads" not in tables:
            print("Migrating: Renaming import_logs to uploads...")
            cursor.execute("ALTER TABLE import_logs RENAME TO uploads;")
            cursor.execute("ALTER TABLE uploads RENAME COLUMN log_id TO upload_id;")
            conn.commit()
            
    except Exception as e:
        print(f"Migration warning: {e}. Attempting full table recreate if needed.")
    finally:
        conn.close()

def initialize_database():
    """
    Creates the 10 core tables required for the enterprise pharmacy platform
    if they do not exist.
    """
    # 1. Run migrations first to protect existing database structures
    migrate_database()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 2. CREATE THE 10 CORE TABLES
    
    # Table 1: tenants
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Table 2: branches
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS branches (
        branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        branch_name TEXT NOT NULL,
        location TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
    );
    """)
    
    # Table 3: users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        branch_id INTEGER,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('Admin', 'Manager', 'Pharmacist')) NOT NULL,
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE SET NULL
    );
    """)
    
    # Table 4: suppliers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        supplier_name TEXT NOT NULL,
        contact_email TEXT,
        contact_phone TEXT,
        avg_lead_time_days REAL DEFAULT 5.0,
        reliability_score REAL DEFAULT 100.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
    );
    """)
    
    # Table 5: medicines
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        medicine_name TEXT NOT NULL,
        bilingual_name TEXT,
        category TEXT,
        unit_price REAL DEFAULT 0.0,
        is_critical INTEGER CHECK(is_critical IN (0, 1)) DEFAULT 0,
        preferred_supplier_id INTEGER,
        min_required_stock INTEGER DEFAULT 20,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        FOREIGN KEY (preferred_supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
        UNIQUE(tenant_id, medicine_name)
    );
    """)
    
    # Table 6: inventory (batch-aware stock)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER NOT NULL,
        branch_id INTEGER NOT NULL,
        batch_number TEXT NOT NULL,
        quantity_stocked INTEGER NOT NULL CHECK(quantity_stocked >= 0),
        expiry_date DATE NOT NULL,
        received_date DATE DEFAULT CURRENT_DATE,
        FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE CASCADE
    );
    """)
    
    # Table 7: sales_history (daily transactions)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_history (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER NOT NULL,
        medicine_id INTEGER NOT NULL,
        quantity_sold INTEGER NOT NULL CHECK(quantity_sold > 0),
        sale_date DATE DEFAULT CURRENT_DATE,
        user_id INTEGER,
        FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE CASCADE,
        FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
    );
    """)
    
    # Table 8: predictions (ML forecast logs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER NOT NULL,
        branch_id INTEGER NOT NULL,
        predicted_date DATE NOT NULL,
        predicted_qty INTEGER DEFAULT 0,
        stockout_date DATE,
        confidence_score REAL DEFAULT 0.0,
        FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE CASCADE
    );
    """)
    
    # Table 9: alerts (inventory risk notifications)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER NOT NULL,
        medicine_id INTEGER NOT NULL,
        alert_type TEXT NOT NULL,
        message TEXT NOT NULL,
        severity TEXT CHECK(severity IN ('Critical', 'High', 'Medium', 'Low')) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE CASCADE,
        FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE
    );
    """)
    
    # Table 10: uploads (data import logs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploads (
        upload_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        branch_id INTEGER NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        filename TEXT NOT NULL,
        records_imported INTEGER DEFAULT 0,
        uploaded_by TEXT NOT NULL,
        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE CASCADE
    );
    """)
    
    # 3. POPULATE SEEDS IF DATABASE IS NEW
    cursor.execute("SELECT COUNT(*) FROM tenants;")
    if cursor.fetchone()[0] == 0:
        print("Database is blank. Seeding default clinic structures...")
        
        # Add Tenant
        cursor.execute("INSERT INTO tenants (company_name) VALUES ('Apex Rural Healthcare Group');")
        tenant_id = cursor.lastrowid
        
        # Add Branch
        cursor.execute("INSERT INTO branches (tenant_id, branch_name, location) VALUES (?, 'PHC Shirur Clinic', 'Pune Rural, MH');", (tenant_id,))
        branch_id = cursor.lastrowid
        
        # Add default users with hashed passwords
        cursor.execute("""
        INSERT INTO users (tenant_id, branch_id, username, password_hash, role, full_name)
        VALUES 
        (?, ?, 'admin', ?, 'Admin', 'Dr. Shridhar Maurya (Director)'),
        (?, ?, 'manager', ?, 'Manager', 'Sneha Patil (Chief Pharmacist)'),
        (?, ?, 'pharmacist', ?, 'Pharmacist', 'Rahul Shinde (Assistant Pharmacist)');
        """, (
            tenant_id, branch_id, hash_password("admin123"),
            tenant_id, branch_id, hash_password("manager123"),
            tenant_id, branch_id, hash_password("pharma123")
        ))
        
        # Add Suppliers
        cursor.execute("""
        INSERT INTO suppliers (tenant_id, supplier_name, contact_email, contact_phone, avg_lead_time_days, reliability_score)
        VALUES 
        (?, 'Maurya Pharma Distributors', 'order@mauryapharma.com', '+91 98234 56781', 4.0, 96.5),
        (?, 'Sahyadri Medical Logistics', 'supply@sahyadrimed.com', '+91 95456 12345', 6.0, 91.0),
        (?, 'Cipla Healthcare Depot', 'dist@ciplahc.com', '+91 88888 77777', 3.0, 98.2),
        (?, 'Bharat Biotech Agency', 'wholesale@bharatbiotech.com', '+91 77777 66666', 8.0, 88.5);
        """, (tenant_id, tenant_id, tenant_id, tenant_id))
        
        # Retrieve supplier dict mapping
        cursor.execute("SELECT supplier_id, supplier_name FROM suppliers;")
        suppliers_dict = {row["supplier_name"]: row["supplier_id"] for row in cursor.fetchall()}
        
        # Default Medicines configurations matching our previous list of 25 formulations
        medicine_seeds = [
            ("Paracetamol 650mg", "पॅरासिटामॉल ६५०mg", "Analgesic (Fever & Pain)", 0, 2.50, "Maurya Pharma Distributors", 30),
            ("Cetirizine 10mg", "सेटिरिझिन १०mg", "Antihistamine (Allergies)", 0, 3.00, "Sahyadri Medical Logistics", 20),
            ("Amoxicillin 500mg", "अमॉक्सिसिलिन ५००mg", "Antibiotic (Infections)", 0, 8.50, "Bharat Biotech Agency", 25),
            ("Insulin Glargine 100IU", "इन्सुलिन ग्लार्जिन १००IU", "Antidiabetic (Critical)", 1, 145.00, "Cipla Healthcare Depot", 15),
            ("Salbutamol Inhaler", "साल्ब्युटामॉल इनहेलर", "Respiratory (Asthma)", 1, 95.00, "Cipla Healthcare Depot", 12),
            ("Phenytoin 100mg", "फेनिटॉइन १००mg", "Anticonvulsant (Epilepsy)", 1, 15.00, "Maurya Pharma Distributors", 10),
            ("ORS (Oral Rehydration)", "ओ.आर.एस (जलसंजीवनी)", "Rehydration (Dehydration)", 0, 4.50, "Sahyadri Medical Logistics", 40),
            ("Cough Syrup 100ml", "खोखल्याचे औषध १००ml", "Respiratory (Cough/Cold)", 0, 45.00, "Maurya Pharma Distributors", 20),
            ("Pantoprazole 40mg", "पॅन्टोप्राझोल ४०mg", "Antacid (Acidity)", 0, 6.00, "Sahyadri Medical Logistics", 25),
            ("Metformin 500mg", "मेटफॉर्मिन ५००mg", "Antidiabetic", 0, 3.50, "Cipla Healthcare Depot", 35)
        ]
        
        for name, mr, cat, crit, price, preferred_supp, min_stock in medicine_seeds:
            supp_id = suppliers_dict.get(preferred_supp)
            cursor.execute("""
            INSERT INTO medicines (tenant_id, medicine_name, bilingual_name, category, is_critical, unit_price, preferred_supplier_id, min_required_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (tenant_id, name, mr, cat, crit, price, supp_id, min_stock))
            med_id = cursor.lastrowid
            
            # Initial stock batches
            # Batch 1: Usable stock
            exp_date_usable = (datetime.now() + timedelta(days=200)).strftime("%Y-%m-%d")
            cursor.execute("""
            INSERT INTO inventory (medicine_id, branch_id, batch_number, quantity_stocked, expiry_date)
            VALUES (?, ?, 'BAT-200A', 120, ?);
            """, (med_id, branch_id, exp_date_usable))
            
            # Batch 2: Deliberate Expired stock for Cetirizine
            if name == "Cetirizine 10mg":
                exp_date_expired = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                cursor.execute("""
                INSERT INTO inventory (medicine_id, branch_id, batch_number, quantity_stocked, expiry_date)
                VALUES (?, ?, 'BAT-EXP99', 30, ?);
                """, (med_id, branch_id, exp_date_expired))
                
            # Batch 3: Deliberate Expiring soon stock for Pantoprazole
            if name == "Pantoprazole 40mg":
                exp_date_soon = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
                cursor.execute("""
                INSERT INTO inventory (medicine_id, branch_id, batch_number, quantity_stocked, expiry_date)
                VALUES (?, ?, 'BAT-SOON1', 20, ?);
                """, (med_id, branch_id, exp_date_soon))
                
            # Critical medicine low stocks seeds
            if name == "Insulin Glargine 100IU":
                # Only 10 units total usable stock left (triggers alerts)
                cursor.execute("UPDATE inventory SET quantity_stocked = 10 WHERE medicine_id = ?;", (med_id,))
                
            # Seed daily usage records (past 60 days) to enable model testing
            np.random.seed(42)
            for day in range(1, 61):
                sale_dt = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
                qty = int(np.random.poisson(15))
                cursor.execute("""
                INSERT INTO sales_history (branch_id, medicine_id, quantity_sold, sale_date)
                VALUES (?, ?, ?, ?);
                """, (branch_id, med_id, qty, sale_dt))
                
    conn.commit()
    conn.close()
    print("Database initialisation and migration sync completed.")

if __name__ == "__main__":
    initialize_database()
