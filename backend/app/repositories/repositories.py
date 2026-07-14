from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from backend.app.repositories.base import BaseRepository
from backend.app.models.models import (
    Tenant, User, Medicine, Inventory, Supplier, Category, Branch, 
    Sale, SaleItem, DemandHistory, Prediction, Alert, 
    Notification, AuditLog, ExpiryTracking, DiseaseTrend, 
    UserSession, ForecastJob, PurchaseOrder
)

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self):
        super().__init__(Medicine)
        
    def get_all_by_tenant(self, db: Session, tenant_id: int) -> List[Medicine]:
        return db.query(Medicine).filter(Medicine.tenant_id == tenant_id).all()

class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self):
        super().__init__(Inventory)
        
    def get_usable_stock(self, db: Session, medicine_id: int, branch_id: int) -> int:
        """Returns sum of unexpired quantity stocked for a medicine in a branch."""
        result = db.query(func.coalesce(func.sum(Inventory.quantity_stocked), 0)).filter(
            Inventory.medicine_id == medicine_id,
            Inventory.branch_id == branch_id,
            Inventory.expiry_date > func.current_date()
        ).scalar()
        return int(result)

    def get_batches(self, db: Session, medicine_id: int, branch_id: int) -> List[Inventory]:
        return db.query(Inventory).filter(
            Inventory.medicine_id == medicine_id,
            Inventory.branch_id == branch_id
        ).order_by(Inventory.expiry_date.asc()).all()

class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self):
        super().__init__(Supplier)

class CategoryRepository(BaseRepository[Category]):
    def __init__(self):
        super().__init__(Category)

class BranchRepository(BaseRepository[Branch]):
    def __init__(self):
        super().__init__(Branch)

class SaleRepository(BaseRepository[Sale]):
    def __init__(self):
        super().__init__(Sale)

class DemandHistoryRepository(BaseRepository[DemandHistory]):
    def __init__(self):
        super().__init__(DemandHistory)
        
    def get_sales_timeline(self, db: Session, medicine_id: int, branch_id: int) -> List[DemandHistory]:
        return db.query(DemandHistory).filter(
            DemandHistory.medicine_id == medicine_id,
            DemandHistory.branch_id == branch_id
        ).order_by(DemandHistory.sale_date.asc()).all()

class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self):
        super().__init__(Prediction)

class AlertRepository(BaseRepository[Alert]):
    def __init__(self):
        super().__init__(Alert)
        
    def get_unresolved_alerts(self, db: Session, branch_id: int) -> List[Alert]:
        return db.query(Alert).filter(
            Alert.branch_id == branch_id,
            Alert.is_resolved == False
        ).all()

class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    def __init__(self):
        super().__init__(PurchaseOrder)

class UserSessionRepository(BaseRepository[UserSession]):
    def __init__(self):
        super().__init__(UserSession)
        
    def get_by_token(self, db: Session, token: str) -> Optional[UserSession]:
        return db.query(UserSession).filter(UserSession.token == token).first()

# Instantiate repos
tenant_repo = BaseRepository(Tenant)
user_repo = UserRepository()
medicine_repo = MedicineRepository()
inventory_repo = InventoryRepository()
supplier_repo = SupplierRepository()
category_repo = CategoryRepository()
branch_repo = BranchRepository()
sale_repo = SaleRepository()
demand_repo = DemandHistoryRepository()
prediction_repo = PredictionRepository()
alert_repo = AlertRepository()
session_repo = UserSessionRepository()
purchase_order_repo = PurchaseOrderRepository()
notification_repo = BaseRepository(Notification)
audit_log_repo = BaseRepository(AuditLog)
expiry_tracking_repo = BaseRepository(ExpiryTracking)
disease_trend_repo = BaseRepository(DiseaseTrend)
forecast_job_repo = BaseRepository(ForecastJob)
