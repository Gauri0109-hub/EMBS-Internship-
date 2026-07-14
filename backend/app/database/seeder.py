from datetime import datetime, timedelta
import numpy as np
import logging
from sqlalchemy.orm import Session
from backend.app.database.session import engine, Base, SessionLocal
from backend.app.models.models import Tenant, Branch, User, Supplier, Medicine, Inventory, DemandHistory
from backend.app.services.auth_service import hash_password

logger = logging.getLogger("pharmacy_platform.seeder")

def seed_database(db: Session):
    """
    Seeds default clinic groups, branches, staff user accounts,
    distributors, medicines, batches, and historical sales transaction records.
    """
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    
    # Check if database is already seeded with both tenants and users
    if db.query(Tenant).count() > 0 and db.query(User).count() > 0:
        logger.info("Database is already seeded. Skipping seeder.")
        return
        
    logger.info("Database is empty or missing users. Seeding default clinic structures...")
    
    # 1. Add default Tenant
    tenant = Tenant(company_name="Apex Rural Healthcare Group")
    db.add(tenant)
    db.flush() # Populate tenant_id
    
    # 2. Add default Branch
    branch = Branch(
        tenant_id=tenant.tenant_id,
        branch_name="PHC Shirur Clinic",
        location="Pune Rural, MH"
    )
    db.add(branch)
    db.flush() # Populate branch_id
    
    # 3. Add default Users
    users = [
        User(
            tenant_id=tenant.tenant_id,
            branch_id=branch.branch_id,
            username="admin",
            password_hash=hash_password("admin123"),
            role="Administrator",
            full_name="Dr. Shridhar Maurya (Director)"
        ),
        User(
            tenant_id=tenant.tenant_id,
            branch_id=branch.branch_id,
            username="manager",
            password_hash=hash_password("manager123"),
            role="Branch Manager",
            full_name="Sneha Patil (Chief Pharmacist)"
        ),
        User(
            tenant_id=tenant.tenant_id,
            branch_id=branch.branch_id,
            username="pharmacist",
            password_hash=hash_password("pharma123"),
            role="Pharmacist",
            full_name="Rahul Shinde (Assistant Pharmacist)"
        )
    ]
    db.add_all(users)
    
    # 4. Add default Suppliers
    suppliers = [
        Supplier(tenant_id=tenant.tenant_id, supplier_name="Maurya Pharma Distributors", contact_email="order@mauryapharma.com", contact_phone="+91 98234 56781", avg_lead_time_days=4.0, reliability_score=96.5),
        Supplier(tenant_id=tenant.tenant_id, supplier_name="Sahyadri Medical Logistics", contact_email="supply@sahyadrimed.com", contact_phone="+91 95456 12345", avg_lead_time_days=6.0, reliability_score=91.0),
        Supplier(tenant_id=tenant.tenant_id, supplier_name="Cipla Healthcare Depot", contact_email="dist@ciplahc.com", contact_phone="+91 88888 77777", avg_lead_time_days=3.0, reliability_score=98.2),
        Supplier(tenant_id=tenant.tenant_id, supplier_name="Bharat Biotech Agency", contact_email="wholesale@bharatbiotech.com", contact_phone="+91 77777 66666", avg_lead_time_days=8.0, reliability_score=88.5)
    ]
    db.add_all(suppliers)
    db.flush()
    
    # Create supplier cache mapping name to id
    supp_cache = {s.supplier_name: s.supplier_id for s in suppliers}
    
    # 5. Default Medicines Configurations (25 formulations)
    medicine_seeds = [
        ("Paracetamol 650mg", "पॅरासिटामॉल ६५०mg", "Analgesic (Fever & Pain)", False, 2.50, "Maurya Pharma Distributors", 30),
        ("Cetirizine 10mg", "सेटिरिझिन १०mg", "Antihistamine (Allergies)", False, 3.00, "Sahyadri Medical Logistics", 20),
        ("Amoxicillin 500mg", "अमॉक्सिसिलिन ५००mg", "Antibiotic (Infections)", False, 8.50, "Bharat Biotech Agency", 25),
        ("Insulin Glargine 100IU", "इन्सुलिन ग्लार्जिन १००IU", "Antidiabetic (Critical)", True, 145.00, "Cipla Healthcare Depot", 15),
        ("Salbutamol Inhaler", "साल्ब्युटामॉल इनहेलर", "Respiratory (Asthma)", True, 95.00, "Cipla Healthcare Depot", 12),
        ("Phenytoin 100mg", "फेनिटॉइन १००mg", "Anticonvulsant (Epilepsy)", True, 15.00, "Maurya Pharma Distributors", 10),
        ("ORS (Oral Rehydration)", "ओ.आर.एस (जलसंजीवनी)", "Rehydration (Dehydration)", False, 4.50, "Sahyadri Medical Logistics", 40),
        ("Cough Syrup 100ml", "खोखल्याचे औषध १००ml", "Respiratory (Cough/Cold)", False, 45.00, "Maurya Pharma Distributors", 20),
        ("Pantoprazole 40mg", "पॅन्टोप्राझोल ४०mg", "Antacid (Acidity)", False, 6.00, "Sahyadri Medical Logistics", 25),
        ("Metformin 500mg", "मेटफॉर्मिन ५००mg", "Antidiabetic", False, 3.50, "Cipla Healthcare Depot", 35)
    ]
    
    today = datetime.now().date()
    
    for name, mr, cat, crit, price, preferred_supp, min_stock in medicine_seeds:
        supp_id = supp_cache.get(preferred_supp)
        med = Medicine(
            tenant_id=tenant.tenant_id,
            medicine_name=name,
            bilingual_name=mr,
            unit_price=price,
            is_critical=crit,
            preferred_supplier_id=supp_id,
            min_required_stock=min_stock
        )
        db.add(med)
        db.flush()
        
        # 6. Initial stock batches
        # Usable batch
        usable_exp = today + timedelta(days=200)
        usable_inv = Inventory(
            medicine_id=med.medicine_id,
            branch_id=branch.branch_id,
            batch_number="BAT-200A",
            quantity_stocked=120,
            expiry_date=usable_exp
        )
        db.add(usable_inv)
        
        # Expired stock for Cetirizine
        if name == "Cetirizine 10mg":
            expired_inv = Inventory(
                medicine_id=med.medicine_id,
                branch_id=branch.branch_id,
                batch_number="BAT-EXP99",
                quantity_stocked=30,
                expiry_date=today - timedelta(days=5)
            )
            db.add(expired_inv)
            
        # Expiring stock for Pantoprazole
        if name == "Pantoprazole 40mg":
            expiring_inv = Inventory(
                medicine_id=med.medicine_id,
                branch_id=branch.branch_id,
                batch_number="BAT-SOON1",
                quantity_stocked=20,
                expiry_date=today + timedelta(days=15)
            )
            db.add(expiring_inv)
            
        # Critical low stock for Insulin
        if name == "Insulin Glargine 100IU":
            # Override usable quantity to be very low
            usable_inv.quantity_stocked = 10
            
        # 7. Historical sales (past 60 days) to unlock ML models immediately
        np.random.seed(42)
        for day in range(1, 61):
            sale_dt = today - timedelta(days=day)
            qty = int(np.random.poisson(15))
            history_log = DemandHistory(
                branch_id=branch.branch_id,
                medicine_id=med.medicine_id,
                quantity_sold=qty,
                sale_date=sale_dt
            )
            db.add(history_log)
            
    db.commit()
    logger.info("Database seeding completed successfully.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
