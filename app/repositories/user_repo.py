"""Data-access layer for `User` and `RefreshToken`: raw CRUD/query operations
(no business rules or HTTP concerns), including geographic scope filtering
reused across services and route dependencies.
"""
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple, List
from sqlalchemy import select, func, and_, or_, distinct, update
from sqlalchemy.orm import Session
from app.models.user import User, ScopeLevelEnum
from app.models.token import RefreshToken
from app.models.rbac import Role, Permission
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
        """Fetch user by unique email address (case-insensitive)."""
        stmt = select(User).where(func.lower(User.email) == email.strip().lower())
        return db.scalars(stmt).first()

    @staticmethod
    def list_users(
        db: Session,
        scope_level: Optional[ScopeLevelEnum] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[User], int]:
        """
        List users with filtering and pagination.
        Filters: scope_level, role, is_active, search (email or full_name).
        """
        stmt = select(User)
        count_stmt = select(func.count(distinct(User.id)))

        # Role filter requires join
        if role:
            stmt = stmt.join(User.roles).where(Role.name == role)
            count_stmt = count_stmt.join(User.roles).where(Role.name == role)

        conditions = []
        if scope_level:
            conditions.append(User.scope_level == scope_level)
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if search:
            search_term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        total = db.scalar(count_stmt) or 0

        # Pagination & ordering
        offset = (page - 1) * page_size
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)

        users = list(db.scalars(stmt).unique().all())
        return users, total

    @staticmethod
    def create(db: Session, user_in: UserCreate, roles: Optional[list[Role]] = None) -> User:
        """Create and persist a new user."""
        new_user = User(
            email=user_in.email.strip().lower(),
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            phone=user_in.phone,
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
    def get_role_by_name(db: Session, role_name: str) -> Optional[Role]:
        """Fetch role by name."""
        stmt = select(Role).where(Role.name == role_name)
        return db.scalars(stmt).first()

    @staticmethod
    def get_roles_by_names(db: Session, role_names: List[str]) -> List[Role]:
        """Fetch list of roles by names."""
        stmt = select(Role).where(Role.name.in_(role_names))
        return list(db.scalars(stmt).all())

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
    def revoke_all_user_tokens(db: Session, user_id: UUID) -> int:
        """Revoke all active refresh tokens for a specified user."""
        stmt = (
            update(RefreshToken)
            .where(and_(RefreshToken.user_id == user_id, RefreshToken.revoked == False))
            .values(revoked=True)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount

    @staticmethod
    def is_super_admin(user: User) -> bool:
        """Determines if the user has super admin permissions."""
        return "manage_permissions" in user.permissions or "view_all" in user.permissions or "manage_users" in user.permissions

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
