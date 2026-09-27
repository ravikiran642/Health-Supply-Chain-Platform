"""Business logic service for facility bed management and occupancy tracking."""
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.bed import BedInventory, BedOccupancyLog, BedTypeEnum
from app.models.geography import Facility, District
from app.models.audit import AuditResultEnum
from sqlalchemy import func, or_
from app.schemas.bed import (
    BedCreate,
    BedUpdate,
    BedInventoryResponse,
    BedSummaryResponse,
    BedOccupancyLogResponse,
    BedHistoryListResponse,
    BedMyScopeItem,
    BedMyScopeAggregate,
    BedMyScopeResponse,
)
from app.schemas.common import PaginationMeta
from app.repositories.bed_repo import BedRepository
from app.services.audit_service import AuditService
from app.services.scope_resolver import (
    resolve_scoped_facility_query,
    resolve_scope_name,
    validate_district_filter,
)


class BedService:
    @staticmethod
    def _to_response(bed: BedInventory) -> BedInventoryResponse:
        return BedInventoryResponse(
            id=bed.id,
            facility_id=bed.facility_id,
            bed_type=bed.bed_type,
            total_beds=bed.total_beds,
            occupied_beds=bed.occupied_beds,
            available_beds=max(0, bed.total_beds - bed.occupied_beds),
            is_active=bed.is_active,
            created_at=bed.created_at,
            updated_at=bed.updated_at,
        )

    @classmethod
    def list_facility_beds(
        cls, db: Session, facility_id: UUID
    ) -> List[BedInventoryResponse]:
        beds = BedRepository.list_by_facility(db, facility_id)
        return [cls._to_response(b) for b in beds]

    @classmethod
    def get_facility_summary(
        cls, db: Session, facility_id: UUID
    ) -> BedSummaryResponse:
        beds = BedRepository.list_by_facility(db, facility_id)
        # Summary counts active beds
        active_beds = [b for b in beds if b.is_active]
        total_beds = sum(b.total_beds for b in active_beds)
        total_occupied = sum(b.occupied_beds for b in active_beds)
        total_available = max(0, total_beds - total_occupied)

        return BedSummaryResponse(
            facility_id=facility_id,
            total_beds=total_beds,
            total_occupied=total_occupied,
            total_available=total_available,
            by_type=[cls._to_response(b) for b in beds],
        )

    @classmethod
    def create_bed_type(
        cls,
        db: Session,
        facility_id: UUID,
        payload: BedCreate,
        actor: User,
        ip_address: str,
    ) -> BedInventoryResponse:
        existing = BedRepository.get_by_facility_and_type(
            db, facility_id, payload.bed_type
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bed type '{payload.bed_type.value}' already exists for this facility",
            )

        bed = BedInventory(
            facility_id=facility_id,
            bed_type=payload.bed_type,
            total_beds=payload.total_beds,
            occupied_beds=0,
            is_active=True,
        )
        BedRepository.create(db, bed)

        # Append to occupancy logs
        log = BedOccupancyLog(
            facility_id=facility_id,
            bed_type=payload.bed_type,
            occupied_beds=0,
            total_beds=payload.total_beds,
            recorded_by=actor.id,
        )
        BedRepository.create_log(db, log)

        AuditService.log_event(
            db=db,
            action="bed_type_added",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="bed_inventory",
            resource_id=str(bed.id),
            metadata={
                "facility_id": str(facility_id),
                "bed_type": payload.bed_type.value,
                "total_beds": payload.total_beds,
            },
        )
        db.commit()
        db.refresh(bed)
        return cls._to_response(bed)

    @classmethod
    def update_bed(
        cls,
        db: Session,
        facility_id: UUID,
        bed_type: BedTypeEnum,
        payload: BedUpdate,
        actor: User,
        ip_address: str,
    ) -> BedInventoryResponse:
        bed = BedRepository.get_by_facility_and_type(db, facility_id, bed_type)
        if not bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bed type '{bed_type.value}' not found for this facility",
            )

        old_total = bed.total_beds
        old_occupied = bed.occupied_beds

        new_total = payload.total_beds if payload.total_beds is not None else bed.total_beds
        new_occupied = payload.occupied_beds if payload.occupied_beds is not None else bed.occupied_beds

        # Validate updating total_beds: cannot go below occupied_beds
        if payload.total_beds is not None and new_total < new_occupied:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total beds ({new_total}) cannot be less than occupied beds ({new_occupied})",
            )

        # Validate updating occupied_beds: cannot exceed total_beds
        if payload.occupied_beds is not None and new_occupied > new_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Occupied beds ({new_occupied}) cannot exceed total beds ({new_total})",
            )

        # Apply changes
        bed.total_beds = new_total
        bed.occupied_beds = new_occupied
        bed.updated_at = datetime.now(timezone.utc)

        # Record occupancy log
        log = BedOccupancyLog(
            facility_id=facility_id,
            bed_type=bed_type,
            occupied_beds=new_occupied,
            total_beds=new_total,
            recorded_by=actor.id,
        )
        BedRepository.create_log(db, log)

        # Audit logs for total and/or occupancy updates
        if payload.total_beds is not None and payload.total_beds != old_total:
            AuditService.log_event(
                db=db,
                action="bed_total_updated",
                ip_address=ip_address,
                result=AuditResultEnum.SUCCESS,
                user_id=actor.id,
                resource_type="bed_inventory",
                resource_id=str(bed.id),
                metadata={
                    "facility_id": str(facility_id),
                    "bed_type": bed_type.value,
                    "old_value": old_total,
                    "new_value": new_total,
                },
            )

        if payload.occupied_beds is not None and payload.occupied_beds != old_occupied:
            AuditService.log_event(
                db=db,
                action="bed_occupancy_updated",
                ip_address=ip_address,
                result=AuditResultEnum.SUCCESS,
                user_id=actor.id,
                resource_type="bed_inventory",
                resource_id=str(bed.id),
                metadata={
                    "facility_id": str(facility_id),
                    "bed_type": bed_type.value,
                    "old_value": old_occupied,
                    "new_value": new_occupied,
                },
            )

        db.commit()
        db.refresh(bed)
        return cls._to_response(bed)

    @classmethod
    def deactivate_bed(
        cls,
        db: Session,
        facility_id: UUID,
        bed_type: BedTypeEnum,
        actor: User,
        ip_address: str,
    ) -> BedInventoryResponse:
        bed = BedRepository.get_by_facility_and_type(db, facility_id, bed_type)
        if not bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bed type '{bed_type.value}' not found for this facility",
            )

        if bed.occupied_beds > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deactivate bed type with active occupants ({bed.occupied_beds} occupied). Discharge patients first.",
            )

        bed.is_active = False
        bed.updated_at = datetime.now(timezone.utc)

        log = BedOccupancyLog(
            facility_id=facility_id,
            bed_type=bed_type,
            occupied_beds=bed.occupied_beds,
            total_beds=bed.total_beds,
            recorded_by=actor.id,
        )
        BedRepository.create_log(db, log)

        AuditService.log_event(
            db=db,
            action="bed_deactivated",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="bed_inventory",
            resource_id=str(bed.id),
            metadata={
                "facility_id": str(facility_id),
                "bed_type": bed_type.value,
                "old_value": True,
                "new_value": False,
            },
        )
        db.commit()
        db.refresh(bed)
        return cls._to_response(bed)

    @classmethod
    def activate_bed(
        cls,
        db: Session,
        facility_id: UUID,
        bed_type: BedTypeEnum,
        actor: User,
        ip_address: str,
    ) -> BedInventoryResponse:
        bed = BedRepository.get_by_facility_and_type(db, facility_id, bed_type)
        if not bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bed type '{bed_type.value}' not found for this facility",
            )

        bed.is_active = True
        bed.updated_at = datetime.now(timezone.utc)

        log = BedOccupancyLog(
            facility_id=facility_id,
            bed_type=bed_type,
            occupied_beds=bed.occupied_beds,
            total_beds=bed.total_beds,
            recorded_by=actor.id,
        )
        BedRepository.create_log(db, log)

        AuditService.log_event(
            db=db,
            action="bed_activated",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="bed_inventory",
            resource_id=str(bed.id),
            metadata={
                "facility_id": str(facility_id),
                "bed_type": bed_type.value,
                "old_value": False,
                "new_value": True,
            },
        )
        db.commit()
        db.refresh(bed)
        return cls._to_response(bed)

    @staticmethod
    def list_history(
        db: Session,
        facility_id: UUID,
        bed_type: Optional[BedTypeEnum] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> BedHistoryListResponse:
        items, total = BedRepository.list_logs(
            db=db,
            facility_id=facility_id,
            bed_type=bed_type,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

        res_items = [BedOccupancyLogResponse.model_validate(log) for log in items]
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return BedHistoryListResponse(
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
        search: Optional[str] = None,
    ) -> BedMyScopeResponse:
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

        # Extract all facilities in scope to compute aggregate totals across ALL facilities
        all_facilities = base_query.all()
        all_facility_ids = [f.id for f in all_facilities]

        bed_aggregates_map = {}
        if all_facility_ids:
            bed_stats = (
                db.query(
                    BedInventory.facility_id,
                    func.coalesce(func.sum(BedInventory.total_beds), 0).label("tot_beds"),
                    func.coalesce(func.sum(BedInventory.occupied_beds), 0).label("occ_beds"),
                )
                .filter(
                    BedInventory.facility_id.in_(all_facility_ids),
                    BedInventory.is_active == True,
                )
                .group_by(BedInventory.facility_id)
                .all()
            )
            for row in bed_stats:
                bed_aggregates_map[row.facility_id] = (row.tot_beds, row.occ_beds)

        # Global aggregate totals across ALL facilities in scope
        agg_total_beds = sum(val[0] for val in bed_aggregates_map.values())
        agg_total_occupied = sum(val[1] for val in bed_aggregates_map.values())
        agg_total_available = max(0, agg_total_beds - agg_total_occupied)
        agg_occupancy_rate = (
            round((agg_total_occupied / agg_total_beds) * 100, 2)
            if agg_total_beds > 0
            else 0.0
        )

        aggregate = BedMyScopeAggregate(
            total_facilities=total_items,
            total_beds=agg_total_beds,
            total_occupied=agg_total_occupied,
            total_available=agg_total_available,
            overall_occupancy_rate=agg_occupancy_rate,
        )

        # Paging for items
        paged_facilities = (
            base_query.order_by(Facility.district_id, Facility.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for fac in paged_facilities:
            f_beds, f_occ = bed_aggregates_map.get(fac.id, (0, 0))
            f_avail = max(0, f_beds - f_occ)
            f_rate = round((f_occ / f_beds) * 100, 2) if f_beds > 0 else 0.0

            items.append(
                BedMyScopeItem(
                    facility_id=fac.id,
                    facility_name=fac.name,
                    facility_code=fac.code,
                    district_id=fac.district_id,
                    district_name=fac.district.name if fac.district else "",
                    total_beds=f_beds,
                    occupied_beds=f_occ,
                    available_beds=f_avail,
                    occupancy_rate=f_rate,
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
            action="beds_my_scope_viewed",
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
                "search": search,
            },
        )
        db.commit()

        return BedMyScopeResponse(
            scope_level=user.scope_level.value,
            scope_name=resolve_scope_name(db, user),
            items=items,
            aggregate=aggregate,
            pagination=pagination,
        )

