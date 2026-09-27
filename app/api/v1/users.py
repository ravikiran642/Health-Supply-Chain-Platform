"""User Management controller (Super Admin operations):
provides endpoints to list, retrieve, create, update, deactivate, reactivate,
and reset passwords for users, as well as inspect assigned roles and effective permissions.
All endpoints require specific granular RBAC permissions.
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_client_ip, require_permission
from app.models.user import User, ScopeLevelEnum
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    ResetPasswordResponse,
)
from app.schemas.rbac import RoleResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users with filters and pagination"
)
def list_users(
    request: Request,
    scope_level: Optional[ScopeLevelEnum] = Query(None, description="Filter by scope level"),
    role: Optional[str] = Query(None, description="Filter by role name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by email or full name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    current_user: User = Depends(require_permission("view_users")),
    db: Session = Depends(get_db),
):
    """Retrieve paginated list of users. Requires 'view_users' permission."""
    ip_addr = get_client_ip(request)
    return UserService.list_users(
        db=db,
        actor=current_user,
        ip_address=ip_addr,
        scope_level=scope_level,
        role=role,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single user detail"
)
def get_user(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("view_users")),
    db: Session = Depends(get_db),
):
    """Retrieve details for a single user by ID. Requires 'view_users' permission."""
    ip_addr = get_client_ip(request)
    return UserService.get_user_by_id(
        db=db,
        user_id=user_id,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user"
)
def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(require_permission("create_user")),
    db: Session = Depends(get_db),
):
    """Create a new user with RBAC role assignments. Requires 'create_user' permission."""
    ip_addr = get_client_ip(request)
    return UserService.create_user(
        db=db,
        user_in=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update existing user"
)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(require_permission("update_user")),
    db: Session = Depends(get_db),
):
    """
    Update user's name, email, phone, geographic scope, or roles.
    Password cannot be updated here. Requires 'update_user' permission.
    """
    ip_addr = get_client_ip(request)
    return UserService.update_user(
        db=db,
        user_id=user_id,
        user_in=payload,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate a user account"
)
def deactivate_user(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("deactivate_user")),
    db: Session = Depends(get_db),
):
    """
    Soft-deactivate a user account and revoke all active refresh tokens.
    Admins cannot deactivate their own accounts. Requires 'deactivate_user' permission.
    """
    ip_addr = get_client_ip(request)
    return UserService.deactivate_user(
        db=db,
        user_id=user_id,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivate a user account"
)
def activate_user(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("activate_user")),
    db: Session = Depends(get_db),
):
    """Reactivate a previously deactivated user account. Requires 'activate_user' permission."""
    ip_addr = get_client_ip(request)
    return UserService.activate_user(
        db=db,
        user_id=user_id,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.post(
    "/{user_id}/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin reset user password"
)
def reset_user_password(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("reset_user_password")),
    db: Session = Depends(get_db),
):
    """
    Generates a secure temporary password, marks password change as required,
    revokes existing refresh tokens, and returns the temporary password once.
    Requires 'reset_user_password' permission.
    """
    ip_addr = get_client_ip(request)
    temp_password = UserService.reset_password(
        db=db,
        user_id=user_id,
        actor=current_user,
        ip_address=ip_addr,
    )
    return ResetPasswordResponse(
        temporary_password=temp_password,
        message="Password reset successfully"
    )


@router.get(
    "/{user_id}/roles",
    response_model=List[RoleResponse],
    status_code=status.HTTP_200_OK,
    summary="List user's assigned roles"
)
def get_user_roles(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("view_users")),
    db: Session = Depends(get_db),
):
    """List all roles assigned to a user. Requires 'view_users' permission."""
    ip_addr = get_client_ip(request)
    return UserService.get_user_roles(
        db=db,
        user_id=user_id,
        actor=current_user,
        ip_address=ip_addr,
    )


@router.get(
    "/{user_id}/permissions",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="List user's effective permissions"
)
def get_user_permissions(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("view_users")),
    db: Session = Depends(get_db),
):
    """List consolidated effective permissions for a user. Requires 'view_users' permission."""
    ip_addr = get_client_ip(request)
    return UserService.get_user_permissions(
        db=db,
        user_id=user_id,
        actor=current_user,
        ip_address=ip_addr,
    )
