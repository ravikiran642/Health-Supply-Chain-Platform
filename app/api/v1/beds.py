"""Beds API Router:
Facility bed inventory and occupancy tracking endpoints.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_client_ip,
    require_permission,
    require_facility_scope,
)
from app.models.user import User
from app.models.bed import BedTypeEnum
from app.models.audit import AuditActionEnum, AuditResultEnum
from app.schemas.bed import (
    BedCreate,
    BedUpdate,
    BedInventoryResponse,
    BedSummaryResponse,
    BedHistoryListResponse,
)
from app.services.bed_service import BedService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/beds", tags=["Beds & Occupancy"])


@router.get(
    "/facility/{facility_id}",
    response_model=List[BedInventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all bed types at facility",
)
def list_facility_beds(
    facility_id: UUID,
    current_user: User = Depends(require_permission("view_beds")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """List all bed types and occupancy at a specific facility. Requires 'view_beds' and facility scope."""
    return BedService.list_facility_beds(db=db, facility_id=facility_id)


@router.get(
    "/facility/{facility_id}/summary",
    response_model=BedSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated bed occupancy summary for facility",
)
def get_facility_summary(
    facility_id: UUID,
    current_user: User = Depends(require_permission("view_beds")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Aggregate total, occupied, and available beds across all active wards for a facility."""
    return BedService.get_facility_summary(db=db, facility_id=facility_id)


@router.post(
    "/facility/{facility_id}",
    response_model=BedInventoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new bed type to facility",
)
def add_bed_type(
    facility_id: UUID,
    payload: BedCreate,
    request: Request,
    current_user: User = Depends(require_permission("add_bed")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Register a new bed ward type. Requires 'add_bed' and facility scope."""
    ip_addr = get_client_ip(request)
    return BedService.create_bed_type(
        db=db,
        facility_id=facility_id,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.patch(
    "/facility/{facility_id}/{bed_type}",
    response_model=BedInventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update bed occupancy or total capacity",
)
def update_bed(
    facility_id: UUID,
    bed_type: BedTypeEnum,
    payload: BedUpdate,
    request: Request,
    current_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """
    Update occupied beds or total capacity.
    Permission checks:
    - If total_beds is provided: requires 'add_bed' permission.
    - If occupied_beds is provided: requires 'update_bed_occupancy' permission.
    """
    ip_addr = get_client_ip(request)
    user_perms = set(current_user.permissions)

    if payload.total_beds is not None and "add_bed" not in user_perms:
        AuditService.log_event(
            db=db,
            action=AuditActionEnum.PERMISSION_DENIED,
            ip_address=ip_addr,
            result=AuditResultEnum.DENIED,
            user_id=current_user.id,
            resource_type="bed_inventory",
            resource_id=f"{facility_id}:{bed_type.value}",
            metadata={
                "required_permission": "add_bed",
                "violation": "inline_permission_check",
                "attempted_field": "total_beds",
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: 'add_bed' required to update total_beds",
        )

    if payload.occupied_beds is not None and "update_bed_occupancy" not in user_perms:
        AuditService.log_event(
            db=db,
            action=AuditActionEnum.PERMISSION_DENIED,
            ip_address=ip_addr,
            result=AuditResultEnum.DENIED,
            user_id=current_user.id,
            resource_type="bed_inventory",
            resource_id=f"{facility_id}:{bed_type.value}",
            metadata={
                "required_permission": "update_bed_occupancy",
                "violation": "inline_permission_check",
                "attempted_field": "occupied_beds",
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: 'update_bed_occupancy' required to update occupied_beds",
        )

    return BedService.update_bed(
        db=db,
        facility_id=facility_id,
        bed_type=bed_type,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/facility/{facility_id}/{bed_type}/deactivate",
    response_model=BedInventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate a bed type",
)
def deactivate_bed(
    facility_id: UUID,
    bed_type: BedTypeEnum,
    request: Request,
    current_user: User = Depends(require_permission("deactivate_bed")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Mark a bed type as inactive. Rejected if occupied_beds > 0."""
    ip_addr = get_client_ip(request)
    return BedService.deactivate_bed(
        db=db,
        facility_id=facility_id,
        bed_type=bed_type,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/facility/{facility_id}/{bed_type}/activate",
    response_model=BedInventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivate an inactive bed type",
)
def activate_bed(
    facility_id: UUID,
    bed_type: BedTypeEnum,
    request: Request,
    current_user: User = Depends(require_permission("add_bed")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Reactivate a previously deactivated bed type."""
    ip_addr = get_client_ip(request)
    return BedService.activate_bed(
        db=db,
        facility_id=facility_id,
        bed_type=bed_type,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.get(
    "/facility/{facility_id}/history",
    response_model=BedHistoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get bed occupancy audit log history",
)
def list_history(
    facility_id: UUID,
    bed_type: Optional[BedTypeEnum] = Query(None, description="Filter by bed type"),
    from_date: Optional[datetime] = Query(None, description="Filter logs starting from datetime"),
    to_date: Optional[datetime] = Query(None, description="Filter logs up to datetime"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(require_permission("view_beds")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Retrieve immutable bed occupancy history log. Requires 'view_beds' and facility scope."""
    return BedService.list_history(
        db=db,
        facility_id=facility_id,
        bed_type=bed_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
