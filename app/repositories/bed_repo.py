"""Repository for BedInventory and BedOccupancyLog database queries and mutations."""
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.bed import BedInventory, BedOccupancyLog, BedTypeEnum


class BedRepository:
    @staticmethod
    def get_by_id(db: Session, bed_id: UUID) -> Optional[BedInventory]:
        return db.query(BedInventory).filter(BedInventory.id == bed_id).first()

    @staticmethod
    def get_by_facility_and_type(
        db: Session, facility_id: UUID, bed_type: BedTypeEnum
    ) -> Optional[BedInventory]:
        return (
            db.query(BedInventory)
            .filter(
                BedInventory.facility_id == facility_id,
                BedInventory.bed_type == bed_type,
            )
            .first()
        )

    @staticmethod
    def list_by_facility(db: Session, facility_id: UUID) -> List[BedInventory]:
        return (
            db.query(BedInventory)
            .filter(BedInventory.facility_id == facility_id)
            .order_by(BedInventory.bed_type.asc())
            .all()
        )

    @staticmethod
    def create(db: Session, bed: BedInventory) -> BedInventory:
        db.add(bed)
        db.flush()
        return bed

    @staticmethod
    def create_log(db: Session, log: BedOccupancyLog) -> BedOccupancyLog:
        db.add(log)
        db.flush()
        return log

    @staticmethod
    def list_logs(
        db: Session,
        facility_id: UUID,
        bed_type: Optional[BedTypeEnum] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[BedOccupancyLog], int]:
        query = db.query(BedOccupancyLog).filter(
            BedOccupancyLog.facility_id == facility_id
        )

        if bed_type is not None:
            query = query.filter(BedOccupancyLog.bed_type == bed_type)
        if from_date is not None:
            query = query.filter(BedOccupancyLog.recorded_at >= from_date)
        if to_date is not None:
            query = query.filter(BedOccupancyLog.recorded_at <= to_date)

        total = query.count()
        items = (
            query.order_by(BedOccupancyLog.recorded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total
