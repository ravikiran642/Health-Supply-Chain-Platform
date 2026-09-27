"""Pydantic schemas for inventory batches and stock transactions."""
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List, Any
import enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.inventory import BatchStatusEnum, TransactionTypeEnum
from app.schemas.common import PaginationMeta


class WriteOffReasonEnum(str, enum.Enum):
    EXPIRED = "expired"
    DAMAGED = "damaged"
    CONTAMINATED = "contaminated"
    RECALLED = "recalled"
    OTHER = "other"


class StockReceiveRequest(BaseModel):
    drug_id: UUID = Field(..., description="ID of the drug being received")
    batch_number: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Alphanumeric batch identifier (3-50 chars, dashes/underscores allowed)",
    )
    quantity: int = Field(..., gt=0, le=1000000, description="Quantity received (> 0, max 1,000,000)")
    expiry_date: date = Field(..., description="Batch expiry date (must be strictly in the future)")
    received_at: Optional[datetime] = Field(None, description="Optional timestamp when stock was received")

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, v: date) -> date:
        if v <= date.today():
            raise ValueError("expiry_date must be strictly in the future (greater than today)")
        return v


class StockDispenseRequest(BaseModel):
    drug_id: UUID = Field(..., description="ID of the drug being dispensed")
    quantity: int = Field(..., gt=0, le=1000000, description="Quantity to dispense (> 0, max 1,000,000)")
    reason: Optional[str] = Field(None, max_length=255, description="Optional clinical/dispensing note")


class StockWriteOffRequest(BaseModel):
    batch_id: UUID = Field(..., description="ID of the batch to write off")
    quantity: int = Field(..., gt=0, le=1000000, description="Quantity to write off (> 0, max 1,000,000)")
    reason_category: WriteOffReasonEnum = Field(..., description="Explicit write-off category")
    reason: str = Field(..., min_length=5, max_length=255, description="Reason for write-off (min 5 chars)")


class InventoryBatchResponse(BaseModel):
    id: UUID
    facility_id: UUID
    drug_id: UUID
    drug_name: Optional[str] = None
    batch_number: str
    quantity: int
    expiry_date: date
    received_at: datetime
    status: BatchStatusEnum
    created_at: datetime
    updated_at: datetime
    days_until_expiry: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class StockTransactionResponse(BaseModel):
    id: UUID
    facility_id: UUID
    drug_id: UUID
    drug_name: Optional[str] = None
    batch_id: Optional[UUID] = None
    batch_number: Optional[str] = None
    transaction_type: TransactionTypeEnum
    quantity: int
    reason: Optional[str] = None
    performed_by: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockTransactionListResponse(BaseModel):
    items: List[StockTransactionResponse]
    pagination: PaginationMeta


class DispenseResponse(BaseModel):
    message: str
    total_dispensed: int
    drug_id: UUID
    facility_id: UUID
    remaining_stock: int
    batches_affected: List[Any]


class InventoryMyScopeItem(BaseModel):
    facility_id: UUID
    facility_name: str
    facility_code: str
    district_id: UUID
    district_name: str
    total_batches: int
    total_quantity: int
    expiring_30d_count: int


class InventoryMyScopeAggregate(BaseModel):
    total_facilities: int
    total_batches: int
    total_quantity: int
    total_expiring_30d: int


class InventoryMyScopeResponse(BaseModel):
    scope_level: str
    scope_name: str
    items: List[InventoryMyScopeItem]
    aggregate: InventoryMyScopeAggregate
    pagination: PaginationMeta

