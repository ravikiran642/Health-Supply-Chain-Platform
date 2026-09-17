from typing import Callable, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, ScopeLevelEnum
from app.models.audit import AuditActionEnum, AuditResultEnum
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService

oauth2_scheme = HTTPBearer(auto_error=True)


def get_client_ip(request: Request) -> str:
    """Extract client IP from headers or connection."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def get_current_user(
    request: Request,
    token_auth: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts and validates JWT from Authorization header.
    Returns active User object; raises 401 if invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = token_auth.credentials
    try:
        payload = decode_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")

        if not user_id_str or token_type != "access":
            raise credentials_exception

        user_id = UUID(user_id_str)
    except Exception:
        raise credentials_exception

    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_permission(permission_name: str) -> Callable:
    """
    FastAPI dependency factory enforcing granular permission.
    Logs permission_denied to audit_logs table on failure.
    """
    def permission_checker(
        request: Request,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Super admin with manage_permissions or view_all bypasses
        if UserRepository.is_super_admin(user) or user.has_permission(permission_name):
            return user

        # Permission denied: Audit log and reject
        ip_addr = get_client_ip(request)
        AuditService.log_event(
            db=db,
            action=AuditActionEnum.PERMISSION_DENIED,
            ip_address=ip_addr,
            result=AuditResultEnum.DENIED,
            user_id=user.id,
            resource_type="permission",
            resource_id=permission_name,
            metadata={"required_permission": permission_name}
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted: missing '{permission_name}' permission"
        )

    return permission_checker


# Geographic scope hierarchy rank (higher number = broader geographic jurisdiction)
SCOPE_HIERARCHY = {
    ScopeLevelEnum.PLATFORM: 100,
    ScopeLevelEnum.NATIONAL: 40,
    ScopeLevelEnum.STATE: 30,
    ScopeLevelEnum.DISTRICT: 20,
    ScopeLevelEnum.PHC: 10,
}


def require_scope(required_scope_level: ScopeLevelEnum | str) -> Callable:
    """
    FastAPI dependency checking if user's scope rank matches or exceeds required scope.
    Super Admin bypasses this check.
    """
    if isinstance(required_scope_level, str):
        required_scope_level = ScopeLevelEnum(required_scope_level.lower())

    def scope_checker(
        request: Request,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if UserRepository.is_super_admin(user) or user.scope_level == ScopeLevelEnum.PLATFORM:
            return user

        user_rank = SCOPE_HIERARCHY.get(user.scope_level, 0)
        required_rank = SCOPE_HIERARCHY.get(required_scope_level, 0)

        if user_rank >= required_rank:
            return user

        ip_addr = get_client_ip(request)
        AuditService.log_event(
            db=db,
            action=AuditActionEnum.PERMISSION_DENIED,
            ip_address=ip_addr,
            result=AuditResultEnum.DENIED,
            user_id=user.id,
            resource_type="scope",
            resource_id=required_scope_level.value,
            metadata={
                "user_scope": user.scope_level.value,
                "required_scope": required_scope_level.value
            }
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Requires scope '{required_scope_level.value}' or broader"
        )

    return scope_checker


def require_scope_tenancy(
    target_scope_level: ScopeLevelEnum | str,
    target_scope_id: UUID
) -> Callable:
    """
    Validates that the user's geographic tenant grants authority over target_scope_id.
    Super Admin bypasses all tenancy restrictions.
    """
    if isinstance(target_scope_level, str):
        target_scope_level = ScopeLevelEnum(target_scope_level.lower())

    def tenancy_checker(
        request: Request,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Super Admin / Platform bypasses
        if UserRepository.is_super_admin(user) or user.scope_level == ScopeLevelEnum.PLATFORM:
            return user

        # National scope has national visibility
        if user.scope_level == ScopeLevelEnum.NATIONAL:
            return user

        # Direct scope match check
        if user.scope_level == target_scope_level and user.scope_id == target_scope_id:
            return user

        # Cross-tenant breach attempt: Log and raise 403
        ip_addr = get_client_ip(request)
        AuditService.log_event(
            db=db,
            action=AuditActionEnum.PERMISSION_DENIED,
            ip_address=ip_addr,
            result=AuditResultEnum.DENIED,
            user_id=user.id,
            resource_type=f"{target_scope_level.value}_tenancy",
            resource_id=str(target_scope_id),
            metadata={
                "violation": "cross_tenant_access_attempt",
                "user_scope_id": str(user.scope_id) if user.scope_id else None,
                "target_scope_id": str(target_scope_id),
            }
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have geographic access to this entity"
        )

    return tenancy_checker
