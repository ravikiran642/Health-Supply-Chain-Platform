"""Repository for StaffAttendance database operations."""
from uuid import UUID
from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.attendance import StaffAttendance, AttendanceStatusEnum
from app.models.user import User, ScopeLevelEnum


class AttendanceRepository:
    @staticmethod
    def get_by_id(db: Session, attendance_id: UUID) -> Optional[StaffAttendance]:
        return db.query(StaffAttendance).filter(StaffAttendance.id == attendance_id).first()

    @staticmethod
    def get_by_user_and_date(
        db: Session, user_id: UUID, attendance_date: date
    ) -> Optional[StaffAttendance]:
        return (
            db.query(StaffAttendance)
            .filter(
                StaffAttendance.user_id == user_id,
                StaffAttendance.attendance_date == attendance_date,
            )
            .first()
        )

    @staticmethod
    def list_by_facility_and_date(
        db: Session, facility_id: UUID, attendance_date: date
    ) -> List[StaffAttendance]:
        return (
            db.query(StaffAttendance)
            .filter(
                StaffAttendance.facility_id == facility_id,
                StaffAttendance.attendance_date == attendance_date,
            )
            .all()
        )

    @staticmethod
    def list_phc_users(db: Session, facility_id: UUID) -> List[User]:
        return (
            db.query(User)
            .filter(
                User.scope_level == ScopeLevelEnum.PHC,
                User.scope_id == facility_id,
                User.is_active == True,
            )
            .order_by(User.full_name.asc())
            .all()
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create(db: Session, record: StaffAttendance) -> StaffAttendance:
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def create_bulk(db: Session, records: List[StaffAttendance]) -> List[StaffAttendance]:
        db.add_all(records)
        db.flush()
        return records

    @staticmethod
    def list_history(
        db: Session,
        facility_id: UUID,
        user_id: Optional[UUID] = None,
        status: Optional[AttendanceStatusEnum] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[StaffAttendance], int]:
        query = db.query(StaffAttendance).filter(StaffAttendance.facility_id == facility_id)

        if user_id is not None:
            query = query.filter(StaffAttendance.user_id == user_id)
        if status is not None:
            query = query.filter(StaffAttendance.status == status)
        if from_date is not None:
            query = query.filter(StaffAttendance.attendance_date >= from_date)
        if to_date is not None:
            query = query.filter(StaffAttendance.attendance_date <= to_date)

        total = query.count()
        items = (
            query.order_by(StaffAttendance.attendance_date.desc(), StaffAttendance.recorded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_summary(
        db: Session,
        facility_id: UUID,
        from_date: date,
        to_date: date,
    ) -> List[Tuple[AttendanceStatusEnum, int]]:
        return (
            db.query(StaffAttendance.status, func.count(StaffAttendance.id))
            .filter(
                StaffAttendance.facility_id == facility_id,
                StaffAttendance.attendance_date >= from_date,
                StaffAttendance.attendance_date <= to_date,
            )
            .group_by(StaffAttendance.status)
            .all()
        )
