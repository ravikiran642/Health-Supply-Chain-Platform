"""Pydantic schemas for bed inventory and occupancy tracking."""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.bed import BedTypeEnum
from app.schemas.common import PaginationMeta


class BedCreate(BaseModel):
    bed_type: BedTypeEnum = Field(..., description="Type of hospital bed ward")
    total_beds: int = Field(..., ge=0, le=10000, description="Total bed capacity (0 <= n <= 10,000)")


class BedUpdate(BaseModel):
    occupied_beds: Optional[int] = Field(None, ge=0, description="New occupied bed count")
    total_beds: Optional[int] = Field(None, ge=0, le=10000, description="New total bed count")

    @model_validator(mode="after")
    def check_at_least_one_field_and_bounds(self) -> "BedUpdate":
        if self.occupied_beds is None and self.total_beds is None:
            raise ValueError("At least one of occupied_beds or total_beds must be provided")
        if self.occupied_beds is not None and self.total_beds is not None:
            if self.occupied_beds > self.total_beds:
                raise ValueError("occupied_beds cannot exceed total_beds")
        return self


class BedInventoryResponse(BaseModel):
    id: UUID
    facility_id: UUID
    bed_type: BedTypeEnum
    total_beds: int
    occupied_beds: int
    available_beds: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BedSummaryResponse(BaseModel):
    facility_id: UUID
    total_beds: int
    total_occupied: int
    total_available: int
    by_type: List[BedInventoryResponse]


class BedOccupancyLogResponse(BaseModel):
    id: UUID
    facility_id: UUID
    bed_type: BedTypeEnum
    occupied_beds: int
    total_beds: int
    recorded_by: UUID
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BedHistoryListResponse(BaseModel):
    items: List[BedOccupancyLogResponse]
    pagination: PaginationMeta


class BedMyScopeItem(BaseModel):
    facility_id: UUID
    facility_name: str
    facility_code: str
    district_id: UUID
    district_name: str
    total_beds: int
    occupied_beds: int
    available_beds: int
    occupancy_rate: float


class BedMyScopeAggregate(BaseModel):
    total_facilities: int
    total_beds: int
    total_occupied: int
    total_available: int
    overall_occupancy_rate: float


class BedMyScopeResponse(BaseModel):
    scope_level: str
    scope_name: str
    items: List[BedMyScopeItem]
    aggregate: BedMyScopeAggregate
    pagination: PaginationMeta

