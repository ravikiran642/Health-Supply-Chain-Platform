"""Pydantic schemas for the Drug catalog master."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.drug import DrugCategoryEnum, DrugUnitEnum


class DrugCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Unique drug name")
    category: DrugCategoryEnum = Field(..., description="Therapeutic category")
    unit: DrugUnitEnum = Field(..., description="Dispensing unit")


class DrugResponse(BaseModel):
    id: UUID
    name: str
    category: DrugCategoryEnum
    unit: DrugUnitEnum
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
