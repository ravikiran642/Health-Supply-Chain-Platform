"""Pydantic v2 schemas for Federated Learning rounds, models, and forecasts."""
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.fl import FlRoundStatusEnum, FlNodeLevelEnum
from app.schemas.common import PaginationMeta


class FlRoundTriggerResponse(BaseModel):
    round_number: int
    status: FlRoundStatusEnum
    participating_districts: int
    participating_states: int
    total_samples: int
    duration_seconds: Optional[float] = None
    model_paths: Dict[str, str] = Field(default_factory=dict)


class FlModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    round_id: UUID
    node_level: FlNodeLevelEnum
    node_id: Optional[UUID] = None
    archive_path: str
    serving_path: str
    is_serving: bool
    model_size_bytes: int
    architecture_hash: str
    hyperparameters: Optional[Dict[str, Any]] = None
    training_metrics: Optional[Dict[str, Any]] = None
    sample_count: int
    created_at: datetime


class FlRoundDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    round_number: int
    status: FlRoundStatusEnum
    started_at: datetime
    completed_at: Optional[datetime] = None
    parent_round_id: Optional[UUID] = None
    participating_districts: int
    participating_states: int
    total_samples: int
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    notes: Optional[str] = None
    models: List[FlModelResponse] = Field(default_factory=list)


class FlRoundListResponse(BaseModel):
    items: List[FlRoundDetailResponse]
    pagination: PaginationMeta


class FlStatusResponse(BaseModel):
    latest_round: Optional[FlRoundDetailResponse] = None
    serving_model_paths: Dict[str, str] = Field(default_factory=dict)
    last_forecast_count: int = 0


class ForecastItemResponse(BaseModel):
    forecast_date: date
    predicted_quantity: float


class DrugForecastResponse(BaseModel):
    drug_id: UUID
    drug_name: str
    forecasts: List[ForecastItemResponse]


class FacilityForecastResponse(BaseModel):
    facility_id: UUID
    facility_name: str
    round_number: Optional[int] = None
    generated_at: Optional[datetime] = None
    drugs: List[DrugForecastResponse] = Field(default_factory=list)
