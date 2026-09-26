"""Re-exports all Pydantic schemas (request/response DTOs) for a single
import path, mirroring the app/models/__init__.py aggregation pattern.
"""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    LogoutRequest,
    LogoutResponse,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserProfileResponse,
)
from app.schemas.rbac import (
    RoleResponse,
    PermissionResponse,
)
from app.schemas.audit import (
    AuditLogCreate,
    AuditLogResponse,
)

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "RefreshRequest",
    "RefreshResponse",
    "LogoutRequest",
    "LogoutResponse",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserProfileResponse",
    "RoleResponse",
    "PermissionResponse",
    "AuditLogCreate",
    "AuditLogResponse",
]
