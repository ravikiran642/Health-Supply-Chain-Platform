"""Staff Attendance API Router:
Facility staff daily attendance roster, marking, bulk-marking, corrections, history, and summaries.
"""
from uuid import UUID
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_client_ip,
    require_permission,
    require_facility_scope,
)
from app.models.user import User
from app.models.attendance import AttendanceStatusEnum
from app.schemas.attendance import (
    AttendanceMarkRequest,
    AttendanceBulkMarkRequest,
    AttendanceCorrectionRequest,
    AttendanceResponse,
    RosterItemResponse,
    AttendanceHistoryListResponse,
    AttendanceSummaryResponse,
)
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Staff Attendance"])


@router.get(
    "/facility/{facility_id}/roster",
    response_model=List[RosterItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get staff attendance roster for date",
)
def get_facility_roster(
    facility_id: UUID,
    date_param: Optional[date] = Query(None, alias="date", description="Target attendance date (defaults to today)"),
    current_user: User = Depends(require_permission("view_attendance")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Retrieve full roster of facility PHC staff and their attendance status on target date."""
    target_date = date_param if date_param is not None else date.today()
    return AttendanceService.get_facility_roster(
        db=db, facility_id=facility_id, attendance_date=target_date
    )


@router.post(
    "/facility/{facility_id}/mark",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Mark single user attendance",
)
def mark_attendance(
    facility_id: UUID,
    payload: AttendanceMarkRequest,
    request: Request,
    current_user: User = Depends(require_permission("mark_attendance")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Record attendance for a single facility staff member. Validates user scope, activity, and date."""
    ip_addr = get_client_ip(request)
    return AttendanceService.mark_attendance(
        db=db,
        facility_id=facility_id,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/facility/{facility_id}/bulk-mark",
    response_model=List[AttendanceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk mark facility staff attendance",
)
def bulk_mark_attendance(
    facility_id: UUID,
    payload: AttendanceBulkMarkRequest,
    request: Request,
    current_user: User = Depends(require_permission("mark_attendance")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Atomic bulk marking of staff attendance. Rejects entire batch if any entry fails validation."""
    ip_addr = get_client_ip(request)
    return AttendanceService.bulk_mark_attendance(
        db=db,
        facility_id=facility_id,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/facility/{facility_id}/{attendance_id}/correct",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Correct existing attendance record",
)
def correct_attendance(
    facility_id: UUID,
    attendance_id: UUID,
    payload: AttendanceCorrectionRequest,
    request: Request,
    current_user: User = Depends(require_permission("correct_attendance")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Modify existing attendance with a mandatory justification reason (min 10 chars). Writes old->new audit log."""
    ip_addr = get_client_ip(request)
    return AttendanceService.correct_attendance(
        db=db,
        facility_id=facility_id,
        attendance_id=attendance_id,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.get(
    "/facility/{facility_id}/history",
    response_model=AttendanceHistoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get paginated attendance history",
)
def list_history(
    facility_id: UUID,
    user_id: Optional[UUID] = Query(None, description="Filter by staff user ID"),
    status_filter: Optional[AttendanceStatusEnum] = Query(None, alias="status", description="Filter by status"),
    from_date: Optional[date] = Query(None, description="Filter starting from date"),
    to_date: Optional[date] = Query(None, description="Filter up to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(require_permission("view_attendance")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Paginated attendance history query for facility staff."""
    return AttendanceService.list_history(
        db=db,
        facility_id=facility_id,
        user_id=user_id,
        status=status_filter,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/facility/{facility_id}/summary",
    response_model=AttendanceSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregate attendance summary for date range",
)
def get_summary(
    facility_id: UUID,
    from_date: date = Query(..., description="Start date (inclusive)"),
    to_date: date = Query(..., description="End date (inclusive)"),
    current_user: User = Depends(require_permission("view_attendance")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Aggregate statistics for staff attendance over a date range."""
    return AttendanceService.get_summary(
        db=db,
        facility_id=facility_id,
        from_date=from_date,
        to_date=to_date,
    )
