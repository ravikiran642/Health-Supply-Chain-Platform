"""Business logic service for Staff Attendance tracking."""
from uuid import UUID
from datetime import date, datetime, timezone
from typing import Optional, List
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, ScopeLevelEnum
from app.models.attendance import StaffAttendance, AttendanceStatusEnum
from app.models.geography import Facility, District
from app.models.audit import AuditResultEnum
from sqlalchemy import func, or_
from app.schemas.attendance import (
    AttendanceMarkRequest,
    AttendanceBulkMarkRequest,
    AttendanceCorrectionRequest,
    AttendanceResponse,
    RosterItemResponse,
    AttendanceHistoryListResponse,
    AttendanceSummaryResponse,
    AttendanceMyScopeItem,
    AttendanceMyScopeAggregate,
    AttendanceMyScopeResponse,
)
from app.schemas.common import PaginationMeta
from app.repositories.attendance_repo import AttendanceRepository
from app.services.audit_service import AuditService
from app.services.scope_resolver import (
    resolve_scoped_facility_query,
    resolve_scope_name,
    validate_district_filter,
)


class AttendanceService:
    @staticmethod
    def _validate_user_for_marking(
        user: Optional[User],
        user_id: UUID,
        facility_id: UUID,
    ) -> None:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{user_id}' does not exist",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{user_id}' is deactivated",
            )
        if user.scope_level != ScopeLevelEnum.PHC:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{user_id}' does not have PHC scope (scope: {user.scope_level.value})",
            )
        if user.scope_id != facility_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{user_id}' belongs to facility '{user.scope_id}', not '{facility_id}'",
            )

    @staticmethod
    def _validate_attendance_date(attendance_date: date) -> None:
        if attendance_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark attendance for future date: {attendance_date}",
            )

    @classmethod
    def get_facility_roster(
        cls, db: Session, facility_id: UUID, attendance_date: date
    ) -> List[RosterItemResponse]:
        phc_users = AttendanceRepository.list_phc_users(db, facility_id)
        attendances = AttendanceRepository.list_by_facility_and_date(
            db, facility_id, attendance_date
        )
        att_map = {att.user_id: att for att in attendances}

        roster = []
        for u in phc_users:
            att = att_map.get(u.id)
            roster.append(
                RosterItemResponse(
                    user_id=u.id,
                    full_name=u.full_name,
                    user_email=u.email,
                    status=att.status if att else None,
                    check_in_time=att.check_in_time if att else None,
                    check_out_time=att.check_out_time if att else None,
                    remarks=att.remarks if att else None,
                    attendance_id=att.id if att else None,
                )
            )
        return roster

    @classmethod
    def mark_attendance(
        cls,
        db: Session,
        facility_id: UUID,
        payload: AttendanceMarkRequest,
        actor: User,
        ip_address: str,
    ) -> AttendanceResponse:
        cls._validate_attendance_date(payload.attendance_date)

        target_user = AttendanceRepository.get_user_by_id(db, payload.user_id)
        cls._validate_user_for_marking(target_user, payload.user_id, facility_id)

        # Check duplicate
        existing = AttendanceRepository.get_by_user_and_date(
            db, payload.user_id, payload.attendance_date
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance already recorded for user '{payload.user_id}' on {payload.attendance_date}",
            )

        record = StaffAttendance(
            facility_id=facility_id,
            user_id=payload.user_id,
            attendance_date=payload.attendance_date,
            status=payload.status,
            check_in_time=payload.check_in_time,
            check_out_time=payload.check_out_time,
            remarks=payload.remarks,
            recorded_by=actor.id,
        )
        AttendanceRepository.create(db, record)

        AuditService.log_event(
            db=db,
            action="attendance_marked",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="staff_attendance",
            resource_id=str(record.id),
            metadata={
                "target_user_id": str(payload.user_id),
                "facility_id": str(facility_id),
                "attendance_date": str(payload.attendance_date),
                "status": payload.status.value,
            },
        )
        db.commit()
        db.refresh(record)
        return AttendanceResponse.model_validate(record)

    @classmethod
    def bulk_mark_attendance(
        cls,
        db: Session,
        facility_id: UUID,
        payload: AttendanceBulkMarkRequest,
        actor: User,
        ip_address: str,
    ) -> List[AttendanceResponse]:
        cls._validate_attendance_date(payload.attendance_date)

        seen_users = set()
        records_to_create = []

        # Validate all entries first (all-or-nothing)
        for entry in payload.entries:
            if entry.user_id in seen_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicate entry for user '{entry.user_id}' in batch request",
                )
            seen_users.add(entry.user_id)

            target_user = AttendanceRepository.get_user_by_id(db, entry.user_id)
            cls._validate_user_for_marking(target_user, entry.user_id, facility_id)

            existing = AttendanceRepository.get_by_user_and_date(
                db, entry.user_id, payload.attendance_date
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Attendance already recorded for user '{entry.user_id}' on {payload.attendance_date}",
                )

            records_to_create.append(
                StaffAttendance(
                    facility_id=facility_id,
                    user_id=entry.user_id,
                    attendance_date=payload.attendance_date,
                    status=entry.status,
                    check_in_time=entry.check_in_time,
                    check_out_time=entry.check_out_time,
                    remarks=entry.remarks,
                    recorded_by=actor.id,
                )
            )

        # Insert all in one atomic transaction
        created_records = AttendanceRepository.create_bulk(db, records_to_create)

        AuditService.log_event(
            db=db,
            action="attendance_bulk_marked",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="staff_attendance",
            resource_id=str(facility_id),
            metadata={
                "facility_id": str(facility_id),
                "attendance_date": str(payload.attendance_date),
                "count": len(created_records),
            },
        )
        db.commit()
        for r in created_records:
            db.refresh(r)
        return [AttendanceResponse.model_validate(r) for r in created_records]

    @classmethod
    def correct_attendance(
        cls,
        db: Session,
        facility_id: UUID,
        attendance_id: UUID,
        payload: AttendanceCorrectionRequest,
        actor: User,
        ip_address: str,
    ) -> AttendanceResponse:
        record = AttendanceRepository.get_by_id(db, attendance_id)
        if not record or record.facility_id != facility_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record '{attendance_id}' not found for this facility",
            )

        old_status = record.status.value
        old_check_in = record.check_in_time.isoformat() if record.check_in_time else None
        old_check_out = record.check_out_time.isoformat() if record.check_out_time else None

        record.status = payload.status
        record.check_in_time = payload.check_in_time
        record.check_out_time = payload.check_out_time
        if payload.remarks is not None:
            record.remarks = payload.remarks
        record.last_modified_by = actor.id
        record.last_modified_at = datetime.now(timezone.utc)

        new_status = payload.status.value
        new_check_in = payload.check_in_time.isoformat() if payload.check_in_time else None
        new_check_out = payload.check_out_time.isoformat() if payload.check_out_time else None

        AuditService.log_event(
            db=db,
            action="attendance_corrected",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="staff_attendance",
            resource_id=str(record.id),
            metadata={
                "target_user_id": str(record.user_id),
                "facility_id": str(facility_id),
                "attendance_date": str(record.attendance_date),
                "old_status": old_status,
                "new_status": new_status,
                "old_check_in": old_check_in,
                "new_check_in": new_check_in,
                "old_check_out": old_check_out,
                "new_check_out": new_check_out,
                "reason": payload.reason,
            },
        )
        db.commit()
        db.refresh(record)
        return AttendanceResponse.model_validate(record)

    @classmethod
    def list_history(
        cls,
        db: Session,
        facility_id: UUID,
        user_id: Optional[UUID] = None,
        status: Optional[AttendanceStatusEnum] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AttendanceHistoryListResponse:
        items, total = AttendanceRepository.list_history(
            db=db,
            facility_id=facility_id,
            user_id=user_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

        res_items = [AttendanceResponse.model_validate(item) for item in items]
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return AttendanceHistoryListResponse(
            items=res_items,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=total_pages,
            ),
        )

    @classmethod
    def get_summary(
        cls,
        db: Session,
        facility_id: UUID,
        from_date: date,
        to_date: date,
    ) -> AttendanceSummaryResponse:
        if from_date > to_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_date cannot be greater than to_date",
            )

        counts_by_status = dict(
            AttendanceRepository.get_summary(db, facility_id, from_date, to_date)
        )

        present = counts_by_status.get(AttendanceStatusEnum.PRESENT, 0)
        absent = counts_by_status.get(AttendanceStatusEnum.ABSENT, 0)
        leave = counts_by_status.get(AttendanceStatusEnum.LEAVE, 0)
        half_day = counts_by_status.get(AttendanceStatusEnum.HALF_DAY, 0)
        on_duty = counts_by_status.get(AttendanceStatusEnum.ON_DUTY, 0)

        total_marked = present + absent + leave + half_day + on_duty
        # Effective present = present + on_duty + 0.5 * half_day
        effective_present = present + on_duty + (0.5 * half_day)
        rate = round((effective_present / total_marked) * 100, 2) if total_marked > 0 else 0.0

        return AttendanceSummaryResponse(
            total_marked=total_marked,
            present_count=present,
            absent_count=absent,
            leave_count=leave,
            half_day_count=half_day,
            on_duty_count=on_duty,
            attendance_rate=rate,
        )

    @classmethod
    def get_my_scope_summary(
        cls,
        db: Session,
        user: User,
        ip_address: str,
        page: int = 1,
        page_size: int = 20,
        district_id: Optional[UUID] = None,
        date_param: Optional[date] = None,
        search: Optional[str] = None,
    ) -> AttendanceMyScopeResponse:
        validate_district_filter(db, user, district_id)

        base_query = resolve_scoped_facility_query(db, user)

        if district_id is not None:
            base_query = base_query.filter(Facility.district_id == district_id)

        if search:
            search_term = f"%{search.strip()}%"
            base_query = base_query.filter(
                or_(
                    Facility.name.ilike(search_term),
                    Facility.code.ilike(search_term),
                )
            )

        total_items = base_query.count()

        all_facilities = base_query.all()
        all_facility_ids = [f.id for f in all_facilities]

        target_date = date_param if date_param is not None else date.today()

        # 1. Total staff per facility: active users with scope_level='phc' and scope_id==facility_id
        staff_counts_map = {}
        if all_facility_ids:
            staff_stats = (
                db.query(
                    User.scope_id,
                    func.count(User.id),
                )
                .filter(
                    User.scope_level == ScopeLevelEnum.PHC,
                    User.scope_id.in_(all_facility_ids),
                    User.is_active == True,
                )
                .group_by(User.scope_id)
                .all()
            )
            for fac_id, count in staff_stats:
                staff_counts_map[fac_id] = count

        # 2. Marked counts per facility and status for target_date
        attendance_map = {}
        if all_facility_ids:
            att_stats = (
                db.query(
                    StaffAttendance.facility_id,
                    StaffAttendance.status,
                    func.count(StaffAttendance.id),
                )
                .filter(
                    StaffAttendance.facility_id.in_(all_facility_ids),
                    StaffAttendance.attendance_date == target_date,
                )
                .group_by(StaffAttendance.facility_id, StaffAttendance.status)
                .all()
            )
            for fac_id, att_status, count in att_stats:
                if fac_id not in attendance_map:
                    attendance_map[fac_id] = {}
                attendance_map[fac_id][att_status] = count

        # Compute facility metrics and overall aggregates
        agg_total_staff = sum(staff_counts_map.get(fid, 0) for fid in all_facility_ids)
        agg_total_present = 0
        agg_total_absent = 0
        agg_total_leave = 0
        agg_total_half_day = 0
        agg_total_on_duty = 0
        agg_total_marked = 0

        facility_metrics_map = {}
        for fid in all_facility_ids:
            t_staff = staff_counts_map.get(fid, 0)
            status_dict = attendance_map.get(fid, {})
            pres = status_dict.get(AttendanceStatusEnum.PRESENT, 0)
            abse = status_dict.get(AttendanceStatusEnum.ABSENT, 0)
            leav = status_dict.get(AttendanceStatusEnum.LEAVE, 0)
            half = status_dict.get(AttendanceStatusEnum.HALF_DAY, 0)
            ondu = status_dict.get(AttendanceStatusEnum.ON_DUTY, 0)
            marked = pres + abse + leav + half + ondu
            eff_pres = pres + ondu + (0.5 * half)
            rate = round((eff_pres / marked) * 100, 2) if marked > 0 else 0.0

            facility_metrics_map[fid] = {
                "total_staff": t_staff,
                "present": pres,
                "absent": abse,
                "leave": leav,
                "half_day": half,
                "on_duty": ondu,
                "marked": marked,
                "rate": rate,
            }

            agg_total_present += pres
            agg_total_absent += abse
            agg_total_leave += leav
            agg_total_half_day += half
            agg_total_on_duty += ondu
            agg_total_marked += marked

        agg_eff_pres = agg_total_present + agg_total_on_duty + (0.5 * agg_total_half_day)
        agg_rate = (
            round((agg_eff_pres / agg_total_marked) * 100, 2)
            if agg_total_marked > 0
            else 0.0
        )

        aggregate = AttendanceMyScopeAggregate(
            total_facilities=total_items,
            total_staff=agg_total_staff,
            total_present=agg_total_present,
            total_absent=agg_total_absent,
            total_leave=agg_total_leave,
            total_half_day=agg_total_half_day,
            total_on_duty=agg_total_on_duty,
            total_marked=agg_total_marked,
            overall_attendance_rate=agg_rate,
        )

        paged_facilities = (
            base_query.order_by(Facility.district_id, Facility.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for fac in paged_facilities:
            m = facility_metrics_map.get(
                fac.id,
                {
                    "total_staff": 0,
                    "present": 0,
                    "absent": 0,
                    "leave": 0,
                    "half_day": 0,
                    "on_duty": 0,
                    "marked": 0,
                    "rate": 0.0,
                },
            )
            items.append(
                AttendanceMyScopeItem(
                    facility_id=fac.id,
                    facility_name=fac.name,
                    facility_code=fac.code,
                    district_id=fac.district_id,
                    district_name=fac.district.name if fac.district else "",
                    total_staff=m["total_staff"],
                    present_count=m["present"],
                    absent_count=m["absent"],
                    leave_count=m["leave"],
                    half_day_count=m["half_day"],
                    on_duty_count=m["on_duty"],
                    marked_count=m["marked"],
                    attendance_rate=m["rate"],
                )
            )

        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
        pagination = PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

        AuditService.log_event(
            db=db,
            action="attendance_my_scope_viewed",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=user.id,
            resource_type="scope_dashboard",
            resource_id=None,
            metadata={
                "scope_level": user.scope_level.value,
                "scope_id": str(user.scope_id) if user.scope_id else None,
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "district_filter": str(district_id) if district_id else None,
                "date": str(target_date),
                "search": search,
            },
        )
        db.commit()

        return AttendanceMyScopeResponse(
            scope_level=user.scope_level.value,
            scope_name=resolve_scope_name(db, user),
            items=items,
            aggregate=aggregate,
            pagination=pagination,
        )

