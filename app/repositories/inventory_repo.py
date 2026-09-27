"""Repository for InventoryBatch and StockTransaction operations."""
from uuid import UUID
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from app.models.inventory import (
    InventoryBatch,
    BatchStatusEnum,
    StockTransaction,
    TransactionTypeEnum,
)
from app.models.drug import Drug


class InventoryRepository:
    @staticmethod
    def get_batch_by_id(db: Session, batch_id: UUID) -> Optional[InventoryBatch]:
        return (
            db.query(InventoryBatch)
            .options(joinedload(InventoryBatch.drug))
            .filter(InventoryBatch.id == batch_id)
            .first()
        )

    @staticmethod
    def get_batch(
        db: Session, facility_id: UUID, drug_id: UUID, batch_number: str
    ) -> Optional[InventoryBatch]:
        return (
            db.query(InventoryBatch)
            .options(joinedload(InventoryBatch.drug))
            .filter(
                InventoryBatch.facility_id == facility_id,
                InventoryBatch.drug_id == drug_id,
                InventoryBatch.batch_number == batch_number,
            )
            .first()
        )

    @staticmethod
    def get_batch_by_facility_and_number(
        db: Session, facility_id: UUID, batch_number: str
    ) -> Optional[InventoryBatch]:
        return (
            db.query(InventoryBatch)
            .filter(
                InventoryBatch.facility_id == facility_id,
                InventoryBatch.batch_number == batch_number,
            )
            .first()
        )

    @staticmethod
    def list_facility_batches(
        db: Session,
        facility_id: UUID,
        drug_id: Optional[UUID] = None,
        status: Optional[BatchStatusEnum] = None,
        search: Optional[str] = None,
    ) -> List[InventoryBatch]:
        query = (
            db.query(InventoryBatch)
            .options(joinedload(InventoryBatch.drug))
            .filter(InventoryBatch.facility_id == facility_id)
        )

        if drug_id is not None:
            query = query.filter(InventoryBatch.drug_id == drug_id)
        if status is not None:
            query = query.filter(InventoryBatch.status == status)
        if search:
            term = f"%{search.strip()}%"
            query = query.join(InventoryBatch.drug).filter(
                (InventoryBatch.batch_number.ilike(term)) | (Drug.name.ilike(term))
            )

        return query.order_by(InventoryBatch.expiry_date.asc()).all()

    @staticmethod
    def get_active_batches_fefo(
        db: Session, facility_id: UUID, drug_id: UUID
    ) -> List[InventoryBatch]:
        """Fetch active batches with quantity > 0 sorted FEFO (First-Expired, First-Out)."""
        return (
            db.query(InventoryBatch)
            .filter(
                InventoryBatch.facility_id == facility_id,
                InventoryBatch.drug_id == drug_id,
                InventoryBatch.status == BatchStatusEnum.ACTIVE,
                InventoryBatch.quantity > 0,
            )
            .order_by(InventoryBatch.expiry_date.asc(), InventoryBatch.created_at.asc())
            .with_for_update()
            .all()
        )

    @staticmethod
    def get_expiring_batches(
        db: Session, facility_id: UUID, days: int
    ) -> List[InventoryBatch]:
        today = date.today()
        threshold_date = today + timedelta(days=days)
        return (
            db.query(InventoryBatch)
            .options(joinedload(InventoryBatch.drug))
            .filter(
                InventoryBatch.facility_id == facility_id,
                InventoryBatch.status == BatchStatusEnum.ACTIVE,
                InventoryBatch.expiry_date >= today,
                InventoryBatch.expiry_date <= threshold_date,
            )
            .order_by(InventoryBatch.expiry_date.asc())
            .all()
        )

    @staticmethod
    def create_batch(db: Session, batch: InventoryBatch) -> InventoryBatch:
        db.add(batch)
        db.flush()
        return batch

    @staticmethod
    def create_transaction(db: Session, tx: StockTransaction) -> StockTransaction:
        db.add(tx)
        db.flush()
        return tx

    @staticmethod
    def list_transactions(
        db: Session,
        facility_id: UUID,
        drug_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionTypeEnum] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[StockTransaction], int]:
        query = (
            db.query(StockTransaction)
            .options(
                joinedload(StockTransaction.drug),
                joinedload(StockTransaction.batch),
            )
            .filter(StockTransaction.facility_id == facility_id)
        )

        if drug_id is not None:
            query = query.filter(StockTransaction.drug_id == drug_id)
        if transaction_type is not None:
            query = query.filter(StockTransaction.transaction_type == transaction_type)
        if from_date is not None:
            query = query.filter(StockTransaction.created_at >= from_date)
        if to_date is not None:
            query = query.filter(StockTransaction.created_at <= to_date)

        total = query.count()
        items = (
            query.order_by(StockTransaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total
