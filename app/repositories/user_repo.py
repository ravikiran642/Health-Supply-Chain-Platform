"""Data-access layer for `User` and `RefreshToken`: raw CRUD/query operations
(no business rules or HTTP concerns), including geographic scope filtering
reused across services and route dependencies.
"""
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Sequence
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.user import User, ScopeLevelEnum
from app.models.token import RefreshToken
from app.models.rbac import Role
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Fetch user by ID."""
        stmt = select(User).where(User.id == user_id)
        return db.scalars(stmt).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        stmt = select(User).where(User.email == email.strip().lower())
        return db.scalars(stmt).first()

    @staticmethod
    def create(db: Session, user_in: UserCreate, roles: Optional[list[Role]] = None) -> User:
        """Create and persist a new user."""
        new_user = User(
            email=user_in.email.strip().lower(),
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            scope_level=user_in.scope_level,
            scope_id=user_in.scope_id,
        )
        if roles:
            new_user.roles = roles
        db.add(new_user)
        db.flush()
        return new_user

    @staticmethod
    def get_refresh_token(db: Session, token_hash: str) -> Optional[RefreshToken]:
        """Retrieve refresh token record by hashed value."""
        stmt = select(RefreshToken).where(RefreshToken.token == token_hash)
        return db.scalars(stmt).first()

    @staticmethod
    def create_refresh_token(
        db: Session,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """Persist a new hashed refresh token."""
        token_record = RefreshToken(
            user_id=user_id,
            token=token_hash,
            expires_at=expires_at,
            revoked=False
        )
        db.add(token_record)
        db.flush()
        return token_record

    @staticmethod
    def revoke_refresh_token(db: Session, token_hash: str) -> bool:
        """Revoke a refresh token."""
        stmt = select(RefreshToken).where(RefreshToken.token == token_hash)
        token_record = db.scalars(stmt).first()
        if token_record and not token_record.revoked:
            token_record.revoked = True
            db.flush()
            return True
        return False

    @staticmethod
    def is_super_admin(user: User) -> bool:
        """Determines if the user has super admin permissions."""
        return "manage_permissions" in user.permissions or "view_all" in user.permissions

    @staticmethod
    def apply_scope_filter(query, user: User, target_model, entity_scope_id_col):
        """
        Enforce geographic multi-tenancy at repository layer.
        Super Admin bypasses all scope filtering.
        Other users strictly filter by their scope.
        """
        if UserRepository.is_super_admin(user) or user.scope_level == ScopeLevelEnum.PLATFORM:
            return query

        if user.scope_level == ScopeLevelEnum.NATIONAL:
            # National users see everything within the nation
            return query

        # For state, district, or PHC, filter strictly by scope_id
        return query.where(entity_scope_id_col == user.scope_id)

    @staticmethod
    def get_scoped_users(db: Session, current_user: User) -> Sequence[User]:
        """Retrieve users filtered strictly by the calling user's geographic tenancy."""
        stmt = select(User)
        if UserRepository.is_super_admin(current_user) or current_user.scope_level == ScopeLevelEnum.PLATFORM:
            return db.scalars(stmt).all()

        if current_user.scope_level == ScopeLevelEnum.NATIONAL:
            return db.scalars(stmt).all()

        stmt = stmt.where(
            and_(
                User.scope_level == current_user.scope_level,
                User.scope_id == current_user.scope_id
            )
        )
        return db.scalars(stmt).all()
