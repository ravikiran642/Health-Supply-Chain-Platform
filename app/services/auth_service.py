"""Business logic for authentication: verifies credentials, issues/refreshes/
revokes JWT + refresh token pairs, and records audit events. Called by the
auth route controller; talks to the DB only through UserRepository.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token_string,
    hash_token,
)
from app.models.user import User
from app.models.audit import AuditActionEnum, AuditResultEnum
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    def authenticate(
        db: Session,
        email: str,
        password: str,
        ip_address: str
    ) -> Tuple[str, str, User]:
        """
        Authenticate user credentials, log attempt, and issue token pair.
        """
        user = UserRepository.get_by_email(db, email)

        if not user or not verify_password(password, user.password_hash):
            AuditService.log_event(
                db=db,
                action=AuditActionEnum.LOGIN,
                ip_address=ip_address,
                result=AuditResultEnum.DENIED,
                user_id=user.id if user else None,
                metadata={"reason": "invalid_credentials"}
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            AuditService.log_event(
                db=db,
                action=AuditActionEnum.LOGIN,
                ip_address=ip_address,
                result=AuditResultEnum.DENIED,
                user_id=user.id,
                metadata={"reason": "inactive_account"}
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate access token claims
        role_names = [r.name for r in user.roles]
        permissions = list(user.permissions)
        claims = {
            "scope_level": user.scope_level.value if hasattr(user.scope_level, "value") else str(user.scope_level),
            "scope_id": str(user.scope_id) if user.scope_id else None,
            "roles": role_names,
            "permissions": permissions,
        }
        access_token = create_access_token(
            subject=str(user.id),
            claims=claims,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        # Generate refresh token and save hash
        raw_refresh_token = create_refresh_token_string()
        hashed_refresh = hash_token(raw_refresh_token)
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        UserRepository.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=hashed_refresh,
            expires_at=refresh_expires_at
        )

        # Audit successful login
        AuditService.log_event(
            db=db,
            action=AuditActionEnum.LOGIN,
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=user.id,
        )
        db.commit()

        return access_token, raw_refresh_token, user

    @staticmethod
    def refresh_access_token(
        db: Session,
        raw_refresh_token: str,
        ip_address: str
    ) -> str:
        """
        Validate DB stored refresh token, verify expiry & revocation, issue new access token.
        """
        hashed = hash_token(raw_refresh_token)
        token_record = UserRepository.get_refresh_token(db, hashed)

        if not token_record or not token_record.is_valid:
            AuditService.log_event(
                db=db,
                action="token_refresh",
                ip_address=ip_address,
                result=AuditResultEnum.DENIED,
                user_id=token_record.user_id if token_record else None,
                metadata={"reason": "invalid_or_revoked_token"}
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid, revoked, or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = token_record.user
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated or deleted",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Issue new access token
        claims = {
            "scope_level": user.scope_level.value if hasattr(user.scope_level, "value") else str(user.scope_level),
            "scope_id": str(user.scope_id) if user.scope_id else None,
            "roles": [r.name for r in user.roles],
            "permissions": list(user.permissions),
        }
        new_access_token = create_access_token(
            subject=str(user.id),
            claims=claims,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        AuditService.log_event(
            db=db,
            action="token_refresh",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=user.id,
        )
        db.commit()

        return new_access_token

    @staticmethod
    def logout(
        db: Session,
        raw_refresh_token: str,
        ip_address: str,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Revoke refresh token and record logout audit."""
        hashed = hash_token(raw_refresh_token)
        token_record = UserRepository.get_refresh_token(db, hashed)
        revoked = False

        resolved_user_id = user_id
        if token_record:
            resolved_user_id = token_record.user_id
            token_record.revoked = True
            db.flush()
            revoked = True

        AuditService.log_event(
            db=db,
            action=AuditActionEnum.LOGOUT,
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS if revoked else AuditResultEnum.DENIED,
            user_id=resolved_user_id,
            metadata={"revoked": revoked}
        )
        db.commit()
        return revoked
