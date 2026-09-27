"""ORM models for `inventory_batches` and `stock_transactions`."""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    Enum,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID


class BatchStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"
    DEPLETED = "depleted"


class TransactionTypeEnum(str, enum.Enum):
    RECEIVE = "receive"
    DISPENSE = "dispense"
    WRITE_OFF = "write_off"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    ADJUSTMENT = "adjustment"


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    facility_id = Column(
        GUID(),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    drug_id = Column(
        GUID(),
        ForeignKey("drugs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    batch_number = Column(String(50), nullable=False)
    quantity = Column(
        Integer,
        CheckConstraint("quantity >= 0", name="chk_batch_quantity_positive"),
        nullable=False,
    )
    expiry_date = Column(Date, nullable=False, index=True)
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status = Column(
        Enum(
            BatchStatusEnum,
            name="batch_status_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=BatchStatusEnum.ACTIVE,
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "facility_id", "drug_id", "batch_number", name="uq_facility_drug_batch"
        ),
    )

    facility = relationship("Facility")
    drug = relationship("Drug", back_populates="batches")
    transactions = relationship("StockTransaction", back_populates="batch")


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    facility_id = Column(
        GUID(),
        ForeignKey("facilities.id"),
        nullable=False,
        index=True,
    )
    drug_id = Column(
        GUID(),
        ForeignKey("drugs.id"),
        nullable=False,
        index=True,
    )
    batch_id = Column(
        GUID(),
        ForeignKey("inventory_batches.id"),
        nullable=True,
        index=True,
    )
    transaction_type = Column(
        Enum(
            TransactionTypeEnum,
            name="transaction_type_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    performed_by = Column(
        GUID(),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    facility = relationship("Facility")
    drug = relationship("Drug", back_populates="transactions")
    batch = relationship("InventoryBatch", back_populates="transactions")
    performer = relationship("User")
