"""Business logic for user management and self-profile operations:
validates geographic scope constraints, enforces password complexity,
manages user lifecycle (create, update, activate, deactivate, password reset),
and records non-PII audit events.
"""
import math
import secrets
import string
from uuid import UUID
from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    get_password_hash,
)
from app.models.user import User, ScopeLevelEnum
from app.models.geography import State, District, Facility
from app.models.rbac import Role
from app.models.audit import AuditResultEnum
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserProfileUpdate,
    ChangePasswordRequest,
    UserResponse,
    UserListResponse,
)
from app.schemas.rbac import RoleResponse


def generate_temp_password(length: int = 12) -> str:
    """Generate a high-entropy temporary password meeting complexity requirements."""
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"
    all_chars = upper + lower + digits + special

    pwd = [
        secrets.choice(upper),
        secrets.choice(lower),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    for _ in range(length - 4):
        pwd.append(secrets.choice(all_chars))
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)


class UserService:
    @staticmethod
    def validate_scope_assignment(
        db: Session,
        scope_level: ScopeLevelEnum,
        scope_id: Optional[UUID]
    ) -> None:
        """
        Enforce geographic hierarchy rules:
        - platform/national: scope_id MUST be None
        - state/district/phc: scope_id MUST be provided and point to a valid existing entity
        """
        if scope_level in (ScopeLevelEnum.PLATFORM, ScopeLevelEnum.NATIONAL):
            if scope_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"scope_id must be None for {scope_level.value} scope level"
                )
            return

        if scope_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"scope_id is required for {scope_level.value} scope level"
            )

        if scope_level == ScopeLevelEnum.STATE:
            state = db.query(State).filter_by(id=scope_id).first()
            if not state:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"State with id '{scope_id}' does not exist"
                )
        elif scope_level == ScopeLevelEnum.DISTRICT:
            district = db.query(District).filter_by(id=scope_id).first()
            if not district:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"District with id '{scope_id}' does not exist"
                )
        elif scope_level == ScopeLevelEnum.PHC:
            facility = db.query(Facility).filter_by(id=scope_id).first()
            if not facility:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Facility (PHC/CHC) with id '{scope_id}' does not exist"
                )

    @staticmethod
    def to_user_response(user: User) -> UserResponse:
        """Convert ORM User to UserResponse schema."""
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            scope_level=user.scope_level,
            scope_id=user.scope_id,
            must_change_password=getattr(user, "must_change_password", False),
            roles=[
                RoleResponse(id=r.id, name=r.name, description=r.description)
                for r in user.roles
            ],
            permissions=sorted(list(user.permissions)),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @classmethod
    def list_users(
        cls,
        db: Session,
        actor: User,
        ip_address: str,
        scope_level: Optional[ScopeLevelEnum] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> UserListResponse:
        """Paginated list of users with multi-dimensional filtering."""
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1"
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )

        users, total = UserRepository.list_users(
            db=db,
            scope_level=scope_level,
            role=role,
            is_active=is_active,
            search=search,
            page=page,
            page_size=page_size,
        )

        AuditService.log_event(
            db=db,
            action="view_users",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="users",
            metadata={"total": total, "page": page, "page_size": page_size}
        )
        db.commit()

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return UserListResponse(
            items=[cls.to_user_response(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    def get_user_by_id(
        cls,
        db: Session,
        user_id: UUID,
        actor: User,
        ip_address: str,
    ) -> UserResponse:
        """Fetch single user by ID."""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        AuditService.log_event(
            db=db,
            action="view_user",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(user.id)
        )
        db.commit()

        return cls.to_user_response(user)

    @classmethod
    def create_user(
        cls,
        db: Session,
        user_in: UserCreate,
        actor: User,
        ip_address: str,
    ) -> UserResponse:
        """Create new user with RBAC role assignments and scope validation."""
        # 1. Unique email check (case-insensitive)
        existing = UserRepository.get_by_email(db, user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )

        # 2. Scope validation
        cls.validate_scope_assignment(db, user_in.scope_level, user_in.scope_id)

        # 3. Role resolution
        if len(user_in.role_names) != 1:
            raise HTTPException(400, "Exactly one role must be assigned")
        resolved_roles = []
        for r_name in user_in.role_names:
            r_obj = UserRepository.get_role_by_name(db, r_name)
            if not r_obj:
                raise HTTPException(400, f"Role '{r_name}' does not exist")
            resolved_roles.append(r_obj)

        # 4. Create user
        new_user = UserRepository.create(db, user_in, resolved_roles)

        # 5. Audit log (non-PII: user IDs and scope metadata only)
        AuditService.log_event(
            db=db,
            action="create_user",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(new_user.id),
            metadata={
                "target_user_id": str(new_user.id),
                "scope_level": new_user.scope_level.value,
                "roles": [r.name for r in resolved_roles]
            }
        )
        db.commit()

        return cls.to_user_response(new_user)

    @classmethod
    def update_user(
        cls,
        db: Session,
        user_id: UUID,
        user_in: UserUpdate,
        actor: User,
        ip_address: str,
    ) -> UserResponse:
        """Update existing user (name, email, phone, scope, roles). Password cannot be changed here."""
        target_user = UserRepository.get_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Email update check
        if user_in.email is not None:
            new_email = user_in.email.strip().lower()
            if new_email != target_user.email.lower():
                existing = UserRepository.get_by_email(db, new_email)
                if existing and existing.id != target_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email is already registered to another user"
                    )
                target_user.email = new_email

        if user_in.full_name is not None:
            target_user.full_name = user_in.full_name.strip()

        if user_in.phone is not None:
            target_user.phone = user_in.phone.strip()

        # Scope update validation
        if user_in.scope_level is not None or user_in.scope_id is not None:
            new_scope_level = user_in.scope_level or target_user.scope_level
            new_scope_id = user_in.scope_id if user_in.scope_id is not None else (
                None if new_scope_level in (ScopeLevelEnum.PLATFORM, ScopeLevelEnum.NATIONAL) else target_user.scope_id
            )
            cls.validate_scope_assignment(db, new_scope_level, new_scope_id)
            target_user.scope_level = new_scope_level
            target_user.scope_id = new_scope_id

        # Roles update
        if user_in.role_names is not None:
            if len(user_in.role_names) != 1:
                raise HTTPException(400, "Exactly one role must be assigned")
            resolved_roles: List[Role] = []
            for r_name in user_in.role_names:
                r_obj = UserRepository.get_role_by_name(db, r_name)
                if not r_obj:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Role '{r_name}' does not exist"
                    )
                resolved_roles.append(r_obj)
            target_user.roles = resolved_roles

        AuditService.log_event(
            db=db,
            action="update_user",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(target_user.id),
            metadata={"target_user_id": str(target_user.id)}
        )
        db.commit()

        return cls.to_user_response(target_user)

    @classmethod
    def deactivate_user(
        cls,
        db: Session,
        user_id: UUID,
        actor: User,
        ip_address: str,
    ) -> UserResponse:
        """Soft-deactivate a user. Cannot deactivate oneself."""
        if actor.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate own account"
            )

        target_user = UserRepository.get_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        target_user.is_active = False
        UserRepository.revoke_all_user_tokens(db, user_id)

        AuditService.log_event(
            db=db,
            action="deactivate_user",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(target_user.id),
            metadata={"target_user_id": str(target_user.id)}
        )
        db.commit()

        return cls.to_user_response(target_user)

    @classmethod
    def activate_user(
        cls,
        db: Session,
        user_id: UUID,
        actor: User,
        ip_address: str,
    ) -> UserResponse:
        """Reactivate a previously deactivated user."""
        target_user = UserRepository.get_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        target_user.is_active = True

        AuditService.log_event(
            db=db,
            action="activate_user",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(target_user.id),
            metadata={"target_user_id": str(target_user.id)}
        )
        db.commit()

        return cls.to_user_response(target_user)

    @classmethod
    def reset_password(
        cls,
        db: Session,
        user_id: UUID,
        actor: User,
        ip_address: str,
    ) -> str:
        """
        Generate temporary password, update password hash, set must_change_password flag,
        revoke all active refresh tokens, and return cleartext temporary password.
        """
        target_user = UserRepository.get_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        temp_password = generate_temp_password(12)
        target_user.password_hash = get_password_hash(temp_password)
        target_user.must_change_password = True

        # Invalidate active refresh tokens for the target user
        UserRepository.revoke_all_user_tokens(db, user_id)

        AuditService.log_event(
            db=db,
            action="reset_user_password",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=actor.id,
            resource_type="user",
            resource_id=str(target_user.id),
            metadata={"target_user_id": str(target_user.id)}
        )
        db.commit()

        return temp_password

    @classmethod
    def get_user_roles(
        cls,
        db: Session,
        user_id: UUID,
        actor: User,
        ip_address: str,
    ) -> List[RoleResponse]:
        """List user's assigned roles."""
        target_user = UserRepository.get_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return [
            RoleResponse(id=r.id, name=r.name, description=r.description)
            for r in target_user.roles
        ]

    @classmethod
    def get_user_permissions(
        cls,
        db: Session,
        user_id: UUID,
        actor: User,
        ip_address: str,
    ) -> List[str]:
        """List user's effective consolidated permissions."""
        target_user = UserRepository.get_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return sorted(list(target_user.permissions))

    @classmethod
    def update_own_profile(
        cls,
        db: Session,
        current_user: User,
        payload: UserProfileUpdate,
        ip_address: str,
    ) -> User:
        """Update authenticated user's own profile (full_name and phone only)."""
        if payload.full_name is not None:
            current_user.full_name = payload.full_name.strip()

        if payload.phone is not None:
            current_user.phone = payload.phone.strip()

        AuditService.log_event(
            db=db,
            action="update_own_profile",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id)
        )
        db.commit()
        return current_user

    @classmethod
    def change_own_password(
        cls,
        db: Session,
        current_user: User,
        payload: ChangePasswordRequest,
        ip_address: str,
    ) -> bool:
        """Change authenticated user's own password."""
        # 1. Verify current password
        if not verify_password(payload.current_password, current_user.password_hash):
            AuditService.log_event(
                db=db,
                action="change_own_password",
                ip_address=ip_address,
                result=AuditResultEnum.DENIED,
                user_id=current_user.id,
                metadata={"reason": "current_password_mismatch"}
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # 2. Ensure new password != current password
        if payload.new_password == payload.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        # 3. Update hash and clear must_change_password flag
        current_user.password_hash = get_password_hash(payload.new_password)
        current_user.must_change_password = False

        AuditService.log_event(
            db=db,
            action="change_own_password",
            ip_address=ip_address,
            result=AuditResultEnum.SUCCESS,
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id)
        )
        db.commit()
        return True
