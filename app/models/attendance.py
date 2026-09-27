"""ORM model for `staff_attendance`."""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Date,
    String,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID


class AttendanceStatusEnum(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LEAVE = "leave"
    HALF_DAY = "half_day"
    ON_DUTY = "on_duty"


class StaffAttendance(Base):
    __tablename__ = "staff_attendance"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    facility_id = Column(
        GUID(),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attendance_date = Column(Date, nullable=False, index=True)
    status = Column(
        Enum(
            AttendanceStatusEnum,
            name="attendance_status_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(String(500), nullable=True)
    recorded_by = Column(
        GUID(),
        ForeignKey("users.id"),
        nullable=False,
    )
    recorded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_modified_by = Column(
        GUID(),
        ForeignKey("users.id"),
        nullable=True,
    )
    last_modified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "attendance_date", name="uq_user_attendance_date"),
        Index("ix_staff_attendance_facility_date", "facility_id", "attendance_date"),
    )

    facility = relationship("Facility")
    user = relationship("User", foreign_keys=[user_id])
    recorder = relationship("User", foreign_keys=[recorded_by])
    modifier = relationship("User", foreign_keys=[last_modified_by])
