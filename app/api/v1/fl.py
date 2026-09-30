"""Federated Learning API Router."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_client_ip,
    require_permission,
    require_any_permission,
)
from app.models.user import User
from app.schemas.fl import (
    FlRoundTriggerResponse,
    FlRoundDetailResponse,
    FlRoundListResponse,
    FlStatusResponse,
    FlModelResponse,
)
from app.services.fl_service import FlService

router = APIRouter(prefix="/fl", tags=["Federated Learning"])


@router.post(
    "/trigger-round",
    response_model=FlRoundTriggerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger a new Federated Learning round across all tiers",
)
def trigger_fl_round(
    request: Request,
    current_user: User = Depends(require_permission("manage_fl")),
    db: Session = Depends(get_db),
):
    """Trigger end-to-end 3-tier hierarchical FL round (Super Admin only)."""
    ip_addr = get_client_ip(request)
    return FlService.trigger_round(db=db, actor=current_user, ip_address=ip_addr)


@router.get(
    "/status",
    response_model=FlStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get status of latest FL round, serving models and forecasts",
)
def get_fl_status(
    current_user: User = Depends(require_any_permission(["manage_fl", "view_fl_model_status"])),
    db: Session = Depends(get_db),
):
    """Get active FL status summary."""
    return FlService.get_status(db=db)


@router.get(
    "/rounds",
    response_model=FlRoundListResponse,
    status_code=status.HTTP_200_OK,
    summary="List paginated historical FL rounds",
)
def list_fl_rounds(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_permission("view_fl_model_status")),
    db: Session = Depends(get_db),
):
    """List historical rounds with pagination."""
    return FlService.list_rounds(db=db, page=page, page_size=page_size)


@router.get(
    "/rounds/{round_id}",
    response_model=FlRoundDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed metrics and per-node models for an FL round",
)
def get_fl_round_detail(
    round_id: UUID,
    current_user: User = Depends(require_permission("view_fl_model_status")),
    db: Session = Depends(get_db),
):
    """Get round details including per-node models across tiers."""
    return FlService.get_round_detail(db=db, round_id=round_id)


@router.get(
    "/models/{model_id}",
    response_model=FlModelResponse,
    status_code=status.HTTP_200_OK,
    summary="Get FL model metadata without exposing raw .pt weights",
)
def get_fl_model_detail(
    model_id: UUID,
    current_user: User = Depends(require_permission("view_fl_metrics")),
    db: Session = Depends(get_db),
):
    """Get metadata for a specific model checkpoint."""
    return FlService.get_model_detail(db=db, model_id=model_id)
