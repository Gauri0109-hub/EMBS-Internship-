from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, 
    ForeignKey, Text, Index, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database.session import Base

# 1. Tenants Table
class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    branches = relationship("Branch", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="tenant", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="tenant", cascade="all, delete-orphan")
    medicines = relationship("Medicine", back_populates="tenant", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="tenant", cascade="all, delete-orphan")


# 2. Branches Table
class Branch(Base):
    __tablename__ = "branches"

    branch_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    branch_name = Column(String(255), nullable=False, index=True)
    location = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="branches")
    users = relationship("User", back_populates="branch")
    inventory = relationship("Inventory", back_populates="branch", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="branch", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="branch", cascade="all, delete-orphan")
    demand_history = relationship("DemandHistory", back_populates="branch", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="branch", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="branch", cascade="all, delete-orphan")
    forecast_jobs = relationship("ForecastJob", back_populates="branch", cascade="all, delete-orphan")


# 3. Users Table
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="SET NULL"), nullable=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)  # Administrator, Pharmacist, Branch Manager, Supplier, Government Officer
    full_name = Column(String(150))
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")
    branch = relationship("Branch", back_populates="users")
    sales = relationship("Sale", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


# 4. Suppliers Table
class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    supplier_name = Column(String(255), nullable=False, index=True)
    contact_email = Column(String(150))
    contact_phone = Column(String(50))
    avg_lead_time_days = Column(Float, default=5.0)
    reliability_score = Column(Float, default=100.0)
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="suppliers")
    medicines = relationship("Medicine", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier", cascade="all, delete-orphan")


# 5. Medicine Categories Table
class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    category_name = Column(String(150), nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="categories")
    medicines = relationship("Medicine", back_populates="category")


# 6. Medicines Table
class Medicine(Base):
    __tablename__ = "medicines"

    medicine_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    medicine_name = Column(String(255), nullable=False, index=True)
    bilingual_name = Column(String(255))
    category_id = Column(Integer, ForeignKey("categories.category_id", ondelete="SET NULL"), nullable=True)
    unit_price = Column(Float, default=0.0)
    is_critical = Column(Boolean, default=False, index=True)
    preferred_supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id", ondelete="SET NULL"), nullable=True)
    min_required_stock = Column(Integer, default=20)
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="medicines")
    category = relationship("Category", back_populates="medicines")
    supplier = relationship("Supplier", back_populates="medicines")
    inventory = relationship("Inventory", back_populates="medicine", cascade="all, delete-orphan")
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="medicine")
    sale_items = relationship("SaleItem", back_populates="medicine")
    demand_history = relationship("DemandHistory", back_populates="medicine", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="medicine", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="medicine", cascade="all, delete-orphan")


# 7. Inventory Table (Batch-aware Stock)
class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False)
    batch_number = Column(String(100), nullable=False, index=True)
    quantity_stocked = Column(Integer, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    received_date = Column(Date, server_default=func.current_date())

    medicine = relationship("Medicine", back_populates="inventory")
    branch = relationship("Branch", back_populates="inventory")
    expiry_tracking = relationship("ExpiryTracking", back_populates="inventory", uselist=False, cascade="all, delete-orphan")


# 8. Purchase Orders Table
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    order_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id", ondelete="CASCADE"), nullable=False)
    order_date = Column(DateTime, server_default=func.now())
    expected_delivery_date = Column(Date)
    status = Column(String(50), default="Pending", index=True)  # Pending, Delivered, Cancelled
    total_cost = Column(Float, default=0.0)

    tenant = relationship("Tenant", back_populates="purchase_orders")
    branch = relationship("Branch", back_populates="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")


# 9. Purchase Order Items Table
class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("purchase_orders.order_id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    medicine = relationship("Medicine", back_populates="purchase_order_items")


# 10. Sales Table
class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    sale_date = Column(DateTime, server_default=func.now(), index=True)
    total_amount = Column(Float, default=0.0)

    branch = relationship("Branch", back_populates="sales")
    user = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


# 11. Sale Items Table
class SaleItem(Base):
    __tablename__ = "sale_items"

    item_id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.sale_id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="items")
    medicine = relationship("Medicine", back_populates="sale_items")


# 12. Demand History Table (Aggregated daily sales logs)
class DemandHistory(Base):
    __tablename__ = "demand_history"

    demand_id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    sale_date = Column(Date, nullable=False, index=True)

    branch = relationship("Branch", back_populates="demand_history")
    medicine = relationship("Medicine", back_populates="demand_history")


# 13. Predictions Table
class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False)
    predicted_date = Column(Date, nullable=False, index=True)
    predicted_qty = Column(Integer, default=0)
    stockout_date = Column(Date, nullable=True)
    confidence_score = Column(Float, default=0.0)

    medicine = relationship("Medicine", back_populates="predictions")
    branch = relationship("Branch", back_populates="predictions")


# 14. Alerts Table (Out of stock / Low stock warnings)
class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(100), nullable=False)  # Out of Stock, Low Stock, Expiry Warning
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, index=True)  # Critical, High, Medium, Low
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    branch = relationship("Branch", back_populates="alerts")
    medicine = relationship("Medicine", back_populates="alerts")


# 15. Notifications Table
class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="notifications")


# 16. Audit Logs Table
class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action = Column(String(150), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User", back_populates="audit_logs")


# 17. Expiry Tracking Table
class ExpiryTracking(Base):
    __tablename__ = "expiry_tracking"

    tracking_id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.inventory_id", ondelete="CASCADE"), nullable=False, unique=True)
    days_to_expiry = Column(Integer, nullable=False)
    risk_status = Column(String(50), nullable=False, index=True)  # Expired, Critical, Warning, Safe

    inventory = relationship("Inventory", back_populates="expiry_tracking")


# 18. Disease Outbreaks / Trends Table
class DiseaseTrend(Base):
    __tablename__ = "disease_trends"

    trend_id = Column(Integer, primary_key=True, index=True)
    region = Column(String(150), nullable=False, index=True)
    disease_name = Column(String(150), nullable=False, index=True)
    outbreak_probability = Column(Float, default=0.0)
    alert_level = Column(String(50), default="Green")  # Red, Orange, Yellow, Green
    date_reported = Column(Date, server_default=func.current_date())


# 19. Sessions Table
class UserSession(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="sessions")


# 20. Forecast Jobs Table
class ForecastJob(Base):
    __tablename__ = "forecast_jobs"

    job_id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="Pending")  # Pending, Running, Completed, Failed
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    branch = relationship("Branch", back_populates="forecast_jobs")


# Composite Indices for optimized querying
Index("idx_dh_branch_med_date", DemandHistory.branch_id, DemandHistory.medicine_id, DemandHistory.sale_date)
Index("idx_inv_branch_med_expiry", Inventory.branch_id, Inventory.medicine_id, Inventory.expiry_date)
