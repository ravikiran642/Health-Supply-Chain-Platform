import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID


class FacilityTypeEnum(str, enum.Enum):
    PHC = "PHC"
    CHC = "CHC"


class State(Base):
    __tablename__ = "states"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)

    districts = relationship("District", back_populates="state", cascade="all, delete-orphan")


class District(Base):
    __tablename__ = "districts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    state_id = Column(GUID(), ForeignKey("states.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)

    state = relationship("State", back_populates="districts")
    facilities = relationship("Facility", back_populates="district", cascade="all, delete-orphan")


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    district_id = Column(GUID(), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    type = Column(
        Enum(
            FacilityTypeEnum,
            name="facility_type_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=FacilityTypeEnum.PHC
    )
    code = Column(String(30), unique=True, nullable=False, index=True)

    district = relationship("District", back_populates="facilities")
