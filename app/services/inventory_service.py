"""Business logic service for Drug catalog and Facility Inventory operations."""
from uuid import UUID
from datetime import date, datetime, timezone
from typing import Optional, List
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.drug import Drug, DrugCategoryEnum, DrugUnitEnum
from app.models.inventory import (
    InventoryBatch,
    BatchStatusEnum,
    StockTransaction,
    TransactionTypeEnum,
)
from app.models.geography import Facility, District
from app.models.audit import AuditResultEnum
from sqlalchemy import func, or_, and_, case
from datetime import timedelta
from app.schemas.drug import DrugCreate, DrugResponse
from app.schemas.inventory import (
    StockReceiveRequest,
    StockDispenseRequest,
    StockWriteOffRequest,
    WriteOffReasonEnum,
    InventoryBatchResponse,
    StockTransactionResponse,
    StockTransactionListResponse,
    DispenseResponse,
    InventoryMyScopeItem,
    InventoryMyScopeAggregate,
    InventoryMyScopeResponse,
)
from app.schemas.common import PaginationMeta
from app.repositories.drug_repo import DrugRepository
from app.repositories.inventory_repo import InventoryRepository
from app.services.audit_service import AuditService
from app.services.scope_resolver import (
    resolve_scoped_facility_query,
    resolve_scope_name,
    validate_district_filter,
)


class InventoryService:
    @staticmethod
    def list_drugs(
        db: Session,
        category: Optional[DrugCategoryEnum] = None,
        unit: Optional[DrugUnitEnum] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[DrugResponse]:
        drugs = DrugRepository.list_drugs(
            db, category=category, unit=unit, is_active=is_active, search=search
        )
        return [DrugResponse.model_validate(d) for d in drugs]

    @staticmethod
    def create_drug(
        db: Session,
        payload: DrugCreate,
        actor: User,
        ip_address: str,
    ) -> DrugResponse:
        existing = DrugRepository.get_by_name(db, payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Drug with name '{payload.name}' already exists",
            )

        drug = DrugRepository.create(db, payload)

        AuditService.log_event(
            db=db,
            action="drug_created",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="drug",
            resource_id=str(drug.id),
            metadata={
                "drug_id": str(drug.id),
                "name": drug.name,
                "category": drug.category.value,
                "unit": drug.unit.value,
            },
        )
        db.commit()
        db.refresh(drug)
        return DrugResponse.model_validate(drug)

    @staticmethod
    def list_facility_batches(
        db: Session,
        facility_id: UUID,
        drug_id: Optional[UUID] = None,
        status_filter: Optional[BatchStatusEnum] = None,
        search: Optional[str] = None,
    ) -> List[InventoryBatchResponse]:
        batches = InventoryRepository.list_facility_batches(
            db=db,
            facility_id=facility_id,
            drug_id=drug_id,
            status=status_filter,
            search=search,
        )
        today = date.today()
        result = []
        for b in batches:
            res = InventoryBatchResponse.model_validate(b)
            res.drug_name = b.drug.name if b.drug else None
            res.days_until_expiry = (b.expiry_date - today).days
            result.append(res)
        return result

    @staticmethod
    def receive_stock(
        db: Session,
        facility_id: UUID,
        payload: StockReceiveRequest,
        actor: User,
        ip_address: str,
    ) -> InventoryBatchResponse:
        drug = DrugRepository.get_by_id(db, payload.drug_id)
        if not drug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Drug not found",
            )
        if not drug.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Drug is inactive",
            )

        if payload.expiry_date <= date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expiry_date must be strictly in the future (greater than today)",
            )

        # Check existing batch with same facility, drug, and batch_number
        batch = InventoryRepository.get_batch(
            db, facility_id, payload.drug_id, payload.batch_number
        )

        if batch:
            batch.quantity += payload.quantity
            if batch.status == BatchStatusEnum.DEPLETED:
                batch.status = BatchStatusEnum.ACTIVE
            batch.updated_at = datetime.now(timezone.utc)
        else:
            # Check edge case: batch number collision with a different drug at same facility
            existing_other = InventoryRepository.get_batch_by_facility_and_number(
                db, facility_id, payload.batch_number
            )
            if existing_other and existing_other.drug_id != payload.drug_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Batch number '{payload.batch_number}' already exists for a different drug at this facility",
                )

            batch = InventoryBatch(
                facility_id=facility_id,
                drug_id=payload.drug_id,
                batch_number=payload.batch_number,
                quantity=payload.quantity,
                expiry_date=payload.expiry_date,
                received_at=payload.received_at or datetime.now(timezone.utc),
                status=BatchStatusEnum.ACTIVE,
            )
            InventoryRepository.create_batch(db, batch)

        # Record immutable transaction
        tx = StockTransaction(
            facility_id=facility_id,
            drug_id=payload.drug_id,
            batch_id=batch.id,
            transaction_type=TransactionTypeEnum.RECEIVE,
            quantity=payload.quantity,  # positive
            reason="Stock receipt",
            performed_by=actor.id,
        )
        InventoryRepository.create_transaction(db, tx)

        AuditService.log_event(
            db=db,
            action="stock_received",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="facility_stock",
            resource_id=str(batch.id),
            metadata={
                "drug_id": str(payload.drug_id),
                "facility_id": str(facility_id),
                "batch_id": str(batch.id),
                "quantity": payload.quantity,
                "transaction_id": str(tx.id),
            },
        )
        db.commit()
        db.refresh(batch)

        res = InventoryBatchResponse.model_validate(batch)
        res.drug_name = drug.name
        res.days_until_expiry = (batch.expiry_date - date.today()).days
        return res

    @staticmethod
    def dispense_stock(
        db: Session,
        facility_id: UUID,
        payload: StockDispenseRequest,
        actor: User,
        ip_address: str,
    ) -> DispenseResponse:
        drug = DrugRepository.get_by_id(db, payload.drug_id)
        if not drug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Drug not found",
            )
        if not drug.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Drug is inactive",
            )

        # Retrieve active batches in FEFO order (earliest expiry first)
        batches = InventoryRepository.get_active_batches_fefo(
            db, facility_id, payload.drug_id
        )
        total_available = sum(b.quantity for b in batches)
        if total_available < payload.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available: {total_available}",
            )

        remaining_to_dispense = payload.quantity
        first_touched_batch_id: Optional[UUID] = None
        batches_affected = []

        for b in batches:
            if remaining_to_dispense <= 0:
                break
            if first_touched_batch_id is None:
                first_touched_batch_id = b.id

            deduct = min(remaining_to_dispense, b.quantity)
            b.quantity -= deduct
            remaining_to_dispense -= deduct

            if b.quantity == 0:
                b.status = BatchStatusEnum.DEPLETED
            b.updated_at = datetime.now(timezone.utc)

            batches_affected.append({
                "batch_id": str(b.id),
                "batch_number": b.batch_number,
                "deducted": deduct,
                "remaining": b.quantity,
                "status": b.status.value,
            })

        tx = StockTransaction(
            facility_id=facility_id,
            drug_id=payload.drug_id,
            batch_id=first_touched_batch_id,
            transaction_type=TransactionTypeEnum.DISPENSE,
            quantity=-payload.quantity,  # negative
            reason=payload.reason or "Dispensed to patient",
            performed_by=actor.id,
        )
        InventoryRepository.create_transaction(db, tx)

        AuditService.log_event(
            db=db,
            action="stock_dispensed",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="facility_stock",
            resource_id=str(first_touched_batch_id),
            metadata={
                "drug_id": str(payload.drug_id),
                "facility_id": str(facility_id),
                "batch_id": str(first_touched_batch_id),
                "quantity": payload.quantity,
                "transaction_id": str(tx.id),
            },
        )
        db.commit()

        remaining_total = total_available - payload.quantity
        return DispenseResponse(
            message="Stock successfully dispensed via FEFO",
            total_dispensed=payload.quantity,
            drug_id=payload.drug_id,
            facility_id=facility_id,
            remaining_stock=remaining_total,
            batches_affected=batches_affected,
        )

    @staticmethod
    def write_off_stock(
        db: Session,
        facility_id: UUID,
        payload: StockWriteOffRequest,
        actor: User,
        ip_address: str,
    ) -> InventoryBatchResponse:
        batch = InventoryRepository.get_batch_by_id(db, payload.batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found",
            )
        if batch.facility_id != facility_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch does not belong to specified facility",
            )
        if batch.status != BatchStatusEnum.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot write off batch with status '{batch.status.value}'",
            )
        if batch.quantity < payload.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient quantity in batch. Available: {batch.quantity}",
            )

        batch.quantity -= payload.quantity
        if batch.quantity == 0:
            if payload.reason_category == WriteOffReasonEnum.EXPIRED:
                batch.status = BatchStatusEnum.EXPIRED
            else:
                batch.status = BatchStatusEnum.DEPLETED
        batch.updated_at = datetime.now(timezone.utc)

        tx = StockTransaction(
            facility_id=facility_id,
            drug_id=batch.drug_id,
            batch_id=batch.id,
            transaction_type=TransactionTypeEnum.WRITE_OFF,
            quantity=-payload.quantity,  # negative
            reason=payload.reason,
            performed_by=actor.id,
        )
        InventoryRepository.create_transaction(db, tx)

        AuditService.log_event(
            db=db,
            action="stock_written_off",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="facility_stock",
            resource_id=str(batch.id),
            metadata={
                "drug_id": str(batch.drug_id),
                "facility_id": str(facility_id),
                "batch_id": str(batch.id),
                "quantity": payload.quantity,
                "transaction_id": str(tx.id),
            },
        )
        db.commit()
        db.refresh(batch)

        res = InventoryBatchResponse.model_validate(batch)
        res.drug_name = batch.drug.name if batch.drug else None
        res.days_until_expiry = (batch.expiry_date - date.today()).days
        return res

    @staticmethod
    def get_expiring_stock(
        db: Session,
        facility_id: UUID,
        days: int = 30,
    ) -> List[InventoryBatchResponse]:
        batches = InventoryRepository.get_expiring_batches(
            db=db, facility_id=facility_id, days=days
        )
        today = date.today()
        result = []
        for b in batches:
            res = InventoryBatchResponse.model_validate(b)
            res.drug_name = b.drug.name if b.drug else None
            res.days_until_expiry = (b.expiry_date - today).days
            result.append(res)
        return result

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
    ) -> StockTransactionListResponse:
        items, total = InventoryRepository.list_transactions(
            db=db,
            facility_id=facility_id,
            drug_id=drug_id,
            transaction_type=transaction_type,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

        res_items = []
        for tx in items:
            tx_res = StockTransactionResponse.model_validate(tx)
            tx_res.drug_name = tx.drug.name if tx.drug else None
            tx_res.batch_number = tx.batch.batch_number if tx.batch else None
            res_items.append(tx_res)

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return StockTransactionListResponse(
             items=res_items,
             pagination=PaginationMeta(
                 page=page,
                 page_size=page_size,
                 total_items=total,
                 total_pages=total_pages,
             ),
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
        drug_id: Optional[UUID] = None,
        search: Optional[str] = None,
    ) -> InventoryMyScopeResponse:
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

        # Extract all facilities in scope
        all_facilities = base_query.all()
        all_facility_ids = [f.id for f in all_facilities]

        inv_aggregates_map = {}
        today = date.today()
        exp_30d = today + timedelta(days=30)

        if all_facility_ids:
            batch_query = db.query(
                InventoryBatch.facility_id,
                func.count(InventoryBatch.id).label("tot_batches"),
                func.coalesce(func.sum(InventoryBatch.quantity), 0).label("tot_qty"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                and_(
                                    InventoryBatch.expiry_date >= today,
                                    InventoryBatch.expiry_date <= exp_30d,
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("exp_30d"),
            ).filter(
                InventoryBatch.facility_id.in_(all_facility_ids),
                InventoryBatch.status == BatchStatusEnum.ACTIVE,
                InventoryBatch.quantity > 0,
            )

            if drug_id is not None:
                batch_query = batch_query.filter(InventoryBatch.drug_id == drug_id)

            batch_stats = batch_query.group_by(InventoryBatch.facility_id).all()
            for row in batch_stats:
                inv_aggregates_map[row.facility_id] = (
                    row.tot_batches,
                    int(row.tot_qty),
                    int(row.exp_30d),
                )

        agg_total_batches = sum(val[0] for val in inv_aggregates_map.values())
        agg_total_quantity = sum(val[1] for val in inv_aggregates_map.values())
        agg_total_expiring_30d = sum(val[2] for val in inv_aggregates_map.values())

        aggregate = InventoryMyScopeAggregate(
            total_facilities=total_items,
            total_batches=agg_total_batches,
            total_quantity=agg_total_quantity,
            total_expiring_30d=agg_total_expiring_30d,
        )

        paged_facilities = (
            base_query.order_by(Facility.district_id, Facility.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for fac in paged_facilities:
            f_batches, f_qty, f_exp = inv_aggregates_map.get(fac.id, (0, 0, 0))
            items.append(
                InventoryMyScopeItem(
                    facility_id=fac.id,
                    facility_name=fac.name,
                    facility_code=fac.code,
                    district_id=fac.district_id,
                    district_name=fac.district.name if fac.district else "",
                    total_batches=f_batches,
                    total_quantity=f_qty,
                    expiring_30d_count=f_exp,
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
            action="inventory_my_scope_viewed",
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
                "drug_id": str(drug_id) if drug_id else None,
                "search": search,
            },
        )
        db.commit()

        return InventoryMyScopeResponse(
            scope_level=user.scope_level.value,
            scope_name=resolve_scope_name(db, user),
            items=items,
            aggregate=aggregate,
            pagination=pagination,
        )

