"""ORM models for `bed_inventories` and `bed_occupancy_logs`."""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID


class BedTypeEnum(str, enum.Enum):
    GENERAL = "general"
    ICU = "icu"
    OXYGEN = "oxygen"
    MATERNITY = "maternity"
    PEDIATRIC = "pediatric"


class BedInventory(Base):
    __tablename__ = "bed_inventories"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    facility_id = Column(
        GUID(),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bed_type = Column(
        Enum(
            BedTypeEnum,
            name="bed_type_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    total_beds = Column(
        Integer,
        CheckConstraint("total_beds >= 0", name="chk_total_beds_positive"),
        nullable=False,
    )
    occupied_beds = Column(
        Integer,
        CheckConstraint("occupied_beds >= 0", name="chk_occupied_beds_positive"),
        nullable=False,
        default=0,
    )
    is_active = Column(Boolean, default=True, nullable=False)
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
        UniqueConstraint("facility_id", "bed_type", name="uq_facility_bed_type"),
        CheckConstraint("occupied_beds <= total_beds", name="chk_occupied_le_total"),
    )

    facility = relationship("Facility")


class BedOccupancyLog(Base):
    __tablename__ = "bed_occupancy_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    facility_id = Column(
        GUID(),
        ForeignKey("facilities.id"),
        nullable=False,
        index=True,
    )
    bed_type = Column(
        Enum(
            BedTypeEnum,
            name="bed_type_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    occupied_beds = Column(Integer, nullable=False)
    total_beds = Column(Integer, nullable=False)
    recorded_by = Column(
        GUID(),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    recorded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    facility = relationship("Facility")
    performer = relationship("User")
