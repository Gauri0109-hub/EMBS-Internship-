from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime

# Config definition for Pydantic v2
class AppBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# Token Schemas
class Token(AppBaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(AppBaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[int] = None
    branch_id: Optional[int] = None


# User Schemas
class UserBase(AppBaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    full_name: Optional[str] = None
    role: str = Field(..., pattern="^(Administrator|Pharmacist|Branch Manager|Supplier|Government Officer)$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    tenant_id: int
    branch_id: Optional[int] = None

class UserUpdate(AppBaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    branch_id: Optional[int] = None
    role: Optional[str] = None

class UserResponse(UserBase):
    user_id: int
    tenant_id: int
    branch_id: Optional[int] = None
    created_at: datetime


# Branch Schemas
class BranchBase(AppBaseModel):
    branch_name: str = Field(..., min_length=2)
    location: Optional[str] = None

class BranchCreate(BranchBase):
    tenant_id: int

class BranchResponse(BranchBase):
    branch_id: int
    tenant_id: int
    created_at: datetime


# Tenant Schemas
class TenantBase(AppBaseModel):
    company_name: str = Field(..., min_length=2)

class TenantCreate(TenantBase):
    admin_username: str
    admin_password: str
    admin_full_name: str

class TenantResponse(TenantBase):
    tenant_id: int
    created_at: datetime


# Supplier Schemas
class SupplierBase(AppBaseModel):
    supplier_name: str = Field(..., min_length=2)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    avg_lead_time_days: Optional[float] = 5.0
    reliability_score: Optional[float] = 100.0

class SupplierCreate(SupplierBase):
    tenant_id: int

class SupplierResponse(SupplierBase):
    supplier_id: int
    tenant_id: int
    created_at: datetime


# Category Schemas
class CategoryBase(AppBaseModel):
    category_name: str = Field(..., min_length=2)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    tenant_id: int

class CategoryResponse(CategoryBase):
    category_id: int
    tenant_id: int
    created_at: datetime


# Medicine Schemas
class MedicineBase(AppBaseModel):
    medicine_name: str = Field(..., min_length=2)
    bilingual_name: Optional[str] = None
    unit_price: float = Field(0.0, ge=0.0)
    is_critical: bool = False
    min_required_stock: int = Field(20, ge=0)

class MedicineCreate(MedicineBase):
    tenant_id: Optional[int] = None
    category_id: Optional[int] = None
    preferred_supplier_id: Optional[int] = None

class MedicineResponse(MedicineBase):
    medicine_id: int
    tenant_id: int
    category_id: Optional[int] = None
    preferred_supplier_id: Optional[int] = None
    created_at: datetime


# Inventory Schemas
class InventoryBase(AppBaseModel):
    medicine_id: int
    batch_number: str = Field(..., min_length=1)
    quantity_stocked: int = Field(..., ge=0)
    expiry_date: date

class InventoryCreate(InventoryBase):
    branch_id: int

class InventoryResponse(InventoryBase):
    inventory_id: int
    branch_id: int
    received_date: date


# Sale & SaleItem Schemas
class SaleItemBase(AppBaseModel):
    medicine_id: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0.0)

class SaleItemCreate(SaleItemBase):
    pass

class SaleItemResponse(SaleItemBase):
    item_id: int
    sale_id: int

class SaleCreate(AppBaseModel):
    items: List[SaleItemCreate]
    sale_date: Optional[datetime] = None

class SaleResponse(AppBaseModel):
    sale_id: int
    branch_id: int
    user_id: Optional[int] = None
    sale_date: datetime
    total_amount: float
    items: List[SaleItemResponse]


# DemandHistory Schemas
class DemandHistoryBase(AppBaseModel):
    branch_id: int
    medicine_id: int
    quantity_sold: int
    sale_date: date

class DemandHistoryResponse(DemandHistoryBase):
    demand_id: int


# Prediction Schemas
class PredictionBase(AppBaseModel):
    medicine_id: int
    branch_id: int
    predicted_date: date
    predicted_qty: int
    stockout_date: Optional[date] = None
    confidence_score: float

class PredictionResponse(PredictionBase):
    prediction_id: int


# Alert Schemas
class AlertBase(AppBaseModel):
    branch_id: int
    medicine_id: int
    alert_type: str
    message: str
    severity: str = Field(..., pattern="^(Critical|High|Medium|Low)$")
    is_resolved: bool = False

class AlertResponse(AlertBase):
    alert_id: int
    created_at: datetime


# Notification Schemas
class NotificationBase(AppBaseModel):
    user_id: int
    title: str
    message: str
    is_read: bool = False

class NotificationResponse(NotificationBase):
    notification_id: int
    created_at: datetime


# AuditLog Schema
class AuditLogResponse(AppBaseModel):
    log_id: int
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    timestamp: datetime


# ExpiryTracking Schema
class ExpiryTrackingResponse(AppBaseModel):
    tracking_id: int
    inventory_id: int
    days_to_expiry: int
    risk_status: str


# DiseaseTrend Schemas
class DiseaseTrendBase(AppBaseModel):
    region: str
    disease_name: str
    outbreak_probability: float
    alert_level: str

class DiseaseTrendCreate(DiseaseTrendBase):
    pass

class DiseaseTrendResponse(DiseaseTrendBase):
    trend_id: int
    date_reported: date


# ForecastJob Schema
class ForecastJobResponse(AppBaseModel):
    job_id: int
    branch_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# PurchaseOrder Schemas
class PurchaseOrderItemBase(AppBaseModel):
    medicine_id: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0.0)

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    item_id: int
    order_id: int

class PurchaseOrderCreate(AppBaseModel):
    supplier_id: int
    expected_delivery_date: Optional[date] = None
    items: List[PurchaseOrderItemCreate]

class PurchaseOrderResponse(AppBaseModel):
    order_id: int
    tenant_id: int
    branch_id: int
    supplier_id: int
    order_date: datetime
    expected_delivery_date: Optional[date] = None
    status: str
    total_cost: float
    items: List[PurchaseOrderItemResponse]


# Chat API Schemas
class ChatMessage(AppBaseModel):
    role: str  # user, assistant
    content: str

class ChatQuery(AppBaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(AppBaseModel):
    reply: str
