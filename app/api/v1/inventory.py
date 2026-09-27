"""Medicine Inventory API Router:
Drug master catalog and facility stock management (receive, dispense via FEFO,
write-off, expiry tracking, and immutable stock transactions ledger).
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import (
    get_client_ip,
    get_current_user,
    require_permission,
    require_scope,
    require_facility_scope,
)
from app.models.user import User, ScopeLevelEnum
from app.models.drug import DrugCategoryEnum, DrugUnitEnum
from app.models.inventory import BatchStatusEnum, TransactionTypeEnum
from app.schemas.drug import DrugCreate, DrugResponse
from app.schemas.inventory import (
    StockReceiveRequest,
    StockDispenseRequest,
    StockWriteOffRequest,
    InventoryBatchResponse,
    StockTransactionListResponse,
    DispenseResponse,
    InventoryMyScopeResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Medicine Inventory"])


# --- DRUG MASTER ---

@router.get(
    "/drugs",
    response_model=List[DrugResponse],
    status_code=status.HTTP_200_OK,
    summary="List all drugs in the catalog",
)
def list_drugs(
    category: Optional[DrugCategoryEnum] = Query(None, description="Filter by therapeutic category"),
    unit: Optional[DrugUnitEnum] = Query(None, description="Filter by dispensing unit"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by drug name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve catalog of drugs. Accessible to any authenticated user."""
    return InventoryService.list_drugs(
        db=db,
        category=category,
        unit=unit,
        is_active=is_active,
        search=search,
    )


@router.post(
    "/drugs",
    response_model=DrugResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new master catalog drug",
)
def create_drug(
    payload: DrugCreate,
    request: Request,
    current_user: User = Depends(require_permission("create_inventory")),
    scoped_user: User = Depends(require_scope(ScopeLevelEnum.PLATFORM)),
    db: Session = Depends(get_db),
):
    """Add a new drug to the master catalog. Requires 'create_inventory' permission and platform scope."""
    ip_addr = get_client_ip(request)
    return InventoryService.create_drug(
        db=db,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


# --- FACILITY STOCK ---

@router.get(
    "/my-scope",
    response_model=InventoryMyScopeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get medicine inventory summary across caller's geographic scope",
)
def get_inventory_my_scope(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    district_id: Optional[UUID] = Query(None, description="Optional district filter within scope"),
    drug_id: Optional[UUID] = Query(None, description="Optional drug filter"),
    search: Optional[str] = Query(None, max_length=100, description="Substring search on facility name or code"),
    current_user: User = Depends(require_permission("view_inventory")),
    db: Session = Depends(get_db),
):
    """Discover facility stock metrics within caller's scope with aggregate totals across all in-scope facilities."""
    ip_addr = get_client_ip(request)
    return InventoryService.get_my_scope_summary(
        db=db,
        user=current_user,
        ip_address=ip_addr,
        page=page,
        page_size=page_size,
        district_id=district_id,
        drug_id=drug_id,
        search=search,
    )


@router.get(
    "/facility/{facility_id}",
    response_model=List[InventoryBatchResponse],
    status_code=status.HTTP_200_OK,
    summary="List stock batches at a facility",
)
def list_facility_stock(
    facility_id: UUID,
    drug_id: Optional[UUID] = Query(None, description="Filter by drug ID"),
    batch_status: Optional[BatchStatusEnum] = Query(None, alias="status", description="Filter by batch status"),
    search: Optional[str] = Query(None, description="Search by batch number or drug name"),
    current_user: User = Depends(require_permission("view_inventory")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """List inventory batches at a facility. Requires 'view_inventory' and facility scope."""
    return InventoryService.list_facility_batches(
        db=db,
        facility_id=facility_id,
        drug_id=drug_id,
        status_filter=batch_status,
        search=search,
    )


@router.post(
    "/facility/{facility_id}/receive",
    response_model=InventoryBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receive medicine stock into facility",
)
def receive_stock(
    facility_id: UUID,
    payload: StockReceiveRequest,
    request: Request,
    current_user: User = Depends(require_permission("create_inventory")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Receive incoming stock for a drug. Requires 'create_inventory' and facility scope."""
    ip_addr = get_client_ip(request)
    return InventoryService.receive_stock(
        db=db,
        facility_id=facility_id,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/facility/{facility_id}/dispense",
    response_model=DispenseResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispense medicine using FEFO",
)
def dispense_stock(
    facility_id: UUID,
    payload: StockDispenseRequest,
    request: Request,
    current_user: User = Depends(require_permission("dispense_medicine")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Dispense stock using First-Expired, First-Out (FEFO) logic. Requires 'dispense_medicine' and facility scope."""
    ip_addr = get_client_ip(request)
    return InventoryService.dispense_stock(
        db=db,
        facility_id=facility_id,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/facility/{facility_id}/write-off",
    response_model=InventoryBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Write off expired or damaged stock batch",
)
def write_off_stock(
    facility_id: UUID,
    payload: StockWriteOffRequest,
    request: Request,
    current_user: User = Depends(require_permission("write_off_stock")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Write off stock from an active batch. Requires 'write_off_stock', a mandatory reason, and facility scope."""
    ip_addr = get_client_ip(request)
    return InventoryService.write_off_stock(
        db=db,
        facility_id=facility_id,
        payload=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.get(
    "/facility/{facility_id}/expiring",
    response_model=List[InventoryBatchResponse],
    status_code=status.HTTP_200_OK,
    summary="List batches expiring within N days",
)
def get_expiring_stock(
    facility_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days lookahead for expiry window"),
    current_user: User = Depends(require_permission("report_expiry")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Retrieve active batches expiring within specified days. Requires 'report_expiry' and facility scope."""
    return InventoryService.get_expiring_stock(
        db=db,
        facility_id=facility_id,
        days=days,
    )


@router.get(
    "/facility/{facility_id}/transactions",
    response_model=StockTransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List immutable stock transaction ledger",
)
def list_stock_transactions(
    facility_id: UUID,
    drug_id: Optional[UUID] = Query(None, description="Filter by drug ID"),
    transaction_type: Optional[TransactionTypeEnum] = Query(None, description="Filter by transaction type"),
    from_date: Optional[datetime] = Query(None, description="Filter from timestamp"),
    to_date: Optional[datetime] = Query(None, description="Filter to timestamp"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(require_permission("view_inventory")),
    scoped_user: User = Depends(require_facility_scope),
    db: Session = Depends(get_db),
):
    """Retrieve immutable audit ledger of stock changes. Requires 'view_inventory' and facility scope."""
    return InventoryService.list_transactions(
        db=db,
        facility_id=facility_id,
        drug_id=drug_id,
        transaction_type=transaction_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
