import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID
from app.models.rbac import user_roles


class ScopeLevelEnum(str, enum.Enum):
    PLATFORM = "platform"
    NATIONAL = "national"
    STATE = "state"
    DISTRICT = "district"
    PHC = "phc"


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    scope_level = Column(
        Enum(ScopeLevelEnum, name="scope_level_enum"),
        nullable=False,
        default=ScopeLevelEnum.PHC,
        index=True
    )
    scope_id = Column(GUID(), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="joined"
    )
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="user"
    )

    @property
    def permissions(self) -> set[str]:
        """Collect unique permission names across all assigned roles."""
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.name)
        return perms

    def has_permission(self, permission_name: str) -> bool:
        """Determines if the user possesses the specified permission."""
        return permission_name in self.permissions
