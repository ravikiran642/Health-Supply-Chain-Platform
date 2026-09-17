import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID, JSONType


class AuditActionEnum(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_DENIED = "permission_denied"
    DATA_ACCESS = "data_access"


class AuditResultEnum(str, enum.Enum):
    SUCCESS = "success"
    DENIED = "denied"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=False)
    result = Column(
        Enum(
            AuditResultEnum,
            name="audit_result_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        index=True
    )
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    metadata_ = Column("metadata", JSONType(), nullable=True)

    user = relationship("User", back_populates="audit_logs")
