"""Auth controller (route layer): defines the /auth/* HTTP endpoints (login,
refresh, logout, me) plus RBAC/tenancy test routes. Delegates all business
logic to AuthService and only handles request/response shaping here.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_client_ip,
    get_current_user,
    require_permission,
    require_scope,
)
from app.models.user import User, ScopeLevelEnum
from app.models.audit import AuditActionEnum, AuditResultEnum
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    LogoutRequest,
    LogoutResponse,
)
from app.schemas.user import UserResponse, UserProfileResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT pair"
)
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate email and password.
    Issues 15-minute access token and 7-day database-hashed refresh token.
    Records audit log event for all attempts.
    """
    ip_addr = get_client_ip(request)
    access_token, refresh_token, user = AuthService.authenticate(
        db=db,
        email=payload.email,
        password=payload.password,
        ip_address=ip_addr
    )

    # Format user response with roles and permissions
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        scope_level=user.scope_level,
        scope_id=user.scope_id,
        roles=[{"id": r.id, "name": r.name, "description": r.description} for r in user.roles],
        permissions=list(user.permissions),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh expired access token with valid refresh token"
)
def refresh(
    request: Request,
    payload: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Validate cryptographic refresh token against hashed database store.
    Issues new access token if valid and unrevoked.
    """
    ip_addr = get_client_ip(request)
    new_access_token = AuthService.refresh_access_token(
        db=db,
        raw_refresh_token=payload.refresh_token,
        ip_address=ip_addr
    )
    return RefreshResponse(
        access_token=new_access_token,
        token_type="bearer"
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke refresh token and terminate session"
)
def logout(
    request: Request,
    payload: LogoutRequest,
    db: Session = Depends(get_db)
):
    """
    Revoke the specified refresh token in the database.
    Prevents any future access token renewals.
    """
    ip_addr = get_client_ip(request)
    AuthService.logout(
        db=db,
        raw_refresh_token=payload.refresh_token,
        ip_address=ip_addr
    )
    return LogoutResponse(
        success=True,
        message="Session terminated and refresh token revoked"
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user's profile and active permissions"
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve currently authenticated user's profile, role assignments,
    geographic scope boundaries, and consolidated permission set.
    """
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        scope_level=current_user.scope_level,
        scope_id=current_user.scope_id,
        roles=[r.name for r in current_user.roles],
        permissions=list(current_user.permissions)
    )


# Protected verification routes demonstrating RBAC & Multi-Tenant Geographic Isolation

@router.post(
    "/test/approve-phc-request",
    status_code=status.HTTP_200_OK,
    summary="Test endpoint requiring 'approve_phc_request' permission"
)
def test_approve_phc_request(
    current_user: User = Depends(require_permission("approve_phc_request"))
):
    """
    RBAC verification endpoint.
    Only PHC Approvers and Super Admins have permission 'approve_phc_request'.
    PHC Operators receive 403 Forbidden and audit_logs are populated.
    """
    return {
        "status": "authorized",
        "action": "approve_phc_request",
        "user_id": str(current_user.id),
        "scope_level": current_user.scope_level.value
    }


@router.get(
    "/test/district-data/{district_id}",
    status_code=status.HTTP_200_OK,
    summary="Test endpoint verifying multi-tenant geographic isolation for district data"
)
def test_district_data(
    district_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("view_district")),
    db: Session = Depends(get_db)
):
    """
    Geographic multi-tenancy verification endpoint.
    A district user from Ramgarh can never access Ranchi district data (403 Forbidden).
    Super Admin bypasses all scope filtering (200 OK).
    """
    # Super admin bypass
    if UserRepository.is_super_admin(current_user) or current_user.scope_level == ScopeLevelEnum.PLATFORM:
        return {
            "status": "authorized",
            "district_id": str(district_id),
            "bypassed": True,
            "access": "full_platform_access"
        }

    # National viewer bypass
    if current_user.scope_level == ScopeLevelEnum.NATIONAL:
        return {
            "status": "authorized",
            "district_id": str(district_id),
            "access": "national_view"
        }

    # Strict multi-tenancy boundary check
    if current_user.scope_level == ScopeLevelEnum.DISTRICT and current_user.scope_id != district_id:
        ip_addr = get_client_ip(request)
        AuditService.log_event(
            db=db,
            action=AuditActionEnum.PERMISSION_DENIED,
            ip_address=ip_addr,
            result=AuditResultEnum.DENIED,
            user_id=current_user.id,
            resource_type="district_data",
            resource_id=str(district_id),
            metadata={
                "violation": "cross_district_access_attempt",
                "user_district_id": str(current_user.scope_id),
                "target_district_id": str(district_id),
            }
        )
        db.commit()
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot access data from a different district"
        )

    return {
        "status": "authorized",
        "district_id": str(district_id),
        "access": "tenant_authorized"
    }
