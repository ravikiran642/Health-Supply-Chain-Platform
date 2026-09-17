import uuid
from sqlalchemy import Column, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID

# Junction table: role_permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        GUID(),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
    Column(
        "permission_id",
        GUID(),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
)

# Junction table: user_roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
    Column(
        "role_id",
        GUID(),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    ),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="joined"
    )
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
