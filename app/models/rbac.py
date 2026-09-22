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


class Role(Base):   # it is a role table in db with columns id, name, description, permissions, and users
    __tablename__ = "roles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    permissions = relationship( # relationship function is used to define the many-to-many relationship between roles and permissions
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="joined"
    )
    users = relationship( # Argument of relationship funciton 1st is the related class name "User", secondary is the junction table user_roles, back_populates is the attribute in User class that refers to roles
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
