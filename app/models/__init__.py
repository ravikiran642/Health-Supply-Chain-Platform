"""Aggregates all SQLAlchemy ORM models so `Base.metadata` is fully populated
for Alembic autogeneration and a single import path is available elsewhere.
"""
from app.core.database import Base
from app.models.geography import State, District, Facility, FacilityTypeEnum
from app.models.rbac import Role, Permission, role_permissions, user_roles
from app.models.user import User, ScopeLevelEnum
from app.models.token import RefreshToken
from app.models.audit import AuditLog, AuditActionEnum, AuditResultEnum
from app.models.drug import Drug, DrugCategoryEnum, DrugUnitEnum
from app.models.inventory import (
    InventoryBatch,
    BatchStatusEnum,
    StockTransaction,
    TransactionTypeEnum,
)
from app.models.bed import (
    BedInventory,
    BedOccupancyLog,
    BedTypeEnum,
)

__all__ = [
    "Base",
    "State",
    "District",
    "Facility",
    "FacilityTypeEnum",
    "Role",
    "Permission",
    "role_permissions",
    "user_roles",
    "User",
    "ScopeLevelEnum",
    "RefreshToken",
    "AuditLog",
    "AuditActionEnum",
    "AuditResultEnum",
    "Drug",
    "DrugCategoryEnum",
    "DrugUnitEnum",
    "InventoryBatch",
    "BatchStatusEnum",
    "StockTransaction",
    "TransactionTypeEnum",
    "BedInventory",
    "BedOccupancyLog",
    "BedTypeEnum",
]
