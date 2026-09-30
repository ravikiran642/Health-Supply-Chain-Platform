"""Data access repository for Federated Learning entities."""
from uuid import UUID
from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.fl import (
    DrugConsumptionHistory,
    FlRound,
    FlModel,
    FlForecast,
    FlRoundStatusEnum,
    FlNodeLevelEnum,
)
from app.models.inventory import StockTransaction, TransactionTypeEnum


class FlRepository:
    @staticmethod
    def get_latest_round(db: Session) -> Optional[FlRound]:
        return db.query(FlRound).order_by(FlRound.round_number.desc()).first()

    @staticmethod
    def get_round_by_id(db: Session, round_id: UUID) -> Optional[FlRound]:
        return db.query(FlRound).filter(FlRound.id == round_id).first()

    @staticmethod
    def list_rounds(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[FlRound], int]:
        query = db.query(FlRound).order_by(FlRound.round_number.desc())
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def get_model_by_id(db: Session, model_id: UUID) -> Optional[FlModel]:
        return db.query(FlModel).filter(FlModel.id == model_id).first()

    @staticmethod
    def get_serving_models(db: Session) -> List[FlModel]:
        return db.query(FlModel).filter(FlModel.is_serving == True).all()

    @staticmethod
    def clear_serving_flags_for_node(db: Session, node_level: FlNodeLevelEnum, node_id: Optional[UUID]) -> None:
        query = db.query(FlModel).filter(
            FlModel.node_level == node_level,
            FlModel.is_serving == True,
        )
        if node_id is not None:
            query = query.filter(FlModel.node_id == node_id)
        else:
            query = query.filter(FlModel.node_id.is_(None))
        query.update({"is_serving": False}, synchronize_session=False)

    @staticmethod
    def get_consumption_history_for_facility_drug(
        db: Session, facility_id: UUID, drug_id: UUID, from_date: Optional[date] = None
    ) -> List[Tuple[date, int]]:
        query = db.query(
            DrugConsumptionHistory.consumption_date,
            DrugConsumptionHistory.quantity_consumed,
        ).filter(
            DrugConsumptionHistory.facility_id == facility_id,
            DrugConsumptionHistory.drug_id == drug_id,
        )
        if from_date is not None:
            query = query.filter(DrugConsumptionHistory.consumption_date >= from_date)
        records = query.order_by(DrugConsumptionHistory.consumption_date.asc()).all()
        return [(r.consumption_date, r.quantity_consumed) for r in records]

    @staticmethod
    def get_district_consumption_history(
        db: Session, district_id: UUID, from_date: Optional[date] = None
    ) -> List[Tuple[date, int]]:
        from app.models.geography import Facility

        query = (
            db.query(
                DrugConsumptionHistory.consumption_date,
                func.sum(DrugConsumptionHistory.quantity_consumed).label("total_qty"),
            )
            .join(Facility, DrugConsumptionHistory.facility_id == Facility.id)
            .filter(Facility.district_id == district_id)
        )
        if from_date is not None:
            query = query.filter(DrugConsumptionHistory.consumption_date >= from_date)

        rows = (
            query.group_by(DrugConsumptionHistory.consumption_date)
            .order_by(DrugConsumptionHistory.consumption_date.asc())
            .all()
        )
        return [(r.consumption_date, int(r.total_qty)) for r in rows]

    @staticmethod
    def rollup_dispense_transactions(db: Session, from_date: date, to_date: date) -> int:
        """
        Aggregate stock_transactions with transaction_type='dispense' into daily totals.
        Upsert into drug_consumption_history. Idempotent.
        """
        # Group transactions by facility_id, drug_id, DATE(created_at)
        daily_tx = (
            db.query(
                StockTransaction.facility_id,
                StockTransaction.drug_id,
                func.date(StockTransaction.created_at).label("tx_date"),
                func.sum(StockTransaction.quantity).label("qty_sum"),
            )
            .filter(
                StockTransaction.transaction_type == TransactionTypeEnum.DISPENSE,
                func.date(StockTransaction.created_at) >= from_date,
                func.date(StockTransaction.created_at) <= to_date,
            )
            .group_by(
                StockTransaction.facility_id,
                StockTransaction.drug_id,
                func.date(StockTransaction.created_at),
            )
            .all()
        )

        upsert_count = 0
        for row in daily_tx:
            rec = (
                db.query(DrugConsumptionHistory)
                .filter(
                    DrugConsumptionHistory.facility_id == row.facility_id,
                    DrugConsumptionHistory.drug_id == row.drug_id,
                    DrugConsumptionHistory.consumption_date == row.tx_date,
                )
                .first()
            )
            if not rec:
                rec = DrugConsumptionHistory(
                    facility_id=row.facility_id,
                    drug_id=row.drug_id,
                    consumption_date=row.tx_date,
                    quantity_consumed=int(row.qty_sum),
                )
                db.add(rec)
            else:
                rec.quantity_consumed = int(row.qty_sum)
            upsert_count += 1

        db.flush()
        return upsert_count

    @staticmethod
    def get_facility_forecasts(
        db: Session,
        facility_id: UUID,
        round_id: Optional[UUID] = None,
        drug_id: Optional[UUID] = None,
        days: int = 7,
    ) -> List[FlForecast]:
        query = db.query(FlForecast).filter(FlForecast.facility_id == facility_id)
        if round_id is not None:
            query = query.filter(FlForecast.round_id == round_id)
        else:
            # Pick latest round with forecasts for this facility
            latest_f = (
                db.query(FlForecast.round_id)
                .filter(FlForecast.facility_id == facility_id)
                .order_by(FlForecast.generated_at.desc())
                .first()
            )
            if latest_f:
                query = query.filter(FlForecast.round_id == latest_f[0])

        if drug_id is not None:
            query = query.filter(FlForecast.drug_id == drug_id)

        return query.order_by(FlForecast.forecast_date.asc()).all()
