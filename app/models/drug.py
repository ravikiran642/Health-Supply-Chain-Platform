"""ORM model for `drugs` (Drug master catalog records)."""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID


class DrugCategoryEnum(str, enum.Enum):
    ANTIBIOTIC = "antibiotic"
    ANALGESIC = "analgesic"
    ANTIMALARIAL = "antimalarial"
    VACCINE = "vaccine"
    ORS = "ors"
    OTHER = "other"


class DrugUnitEnum(str, enum.Enum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    ML = "ml"
    VIAL = "vial"
    SACHET = "sachet"
    TUBE = "tube"


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), unique=True, index=True, nullable=False)
    category = Column(
        Enum(
            DrugCategoryEnum,
            name="drug_category_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    unit = Column(
        Enum(
            DrugUnitEnum,
            name="drug_unit_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
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

    batches = relationship("InventoryBatch", back_populates="drug")
    transactions = relationship("StockTransaction", back_populates="drug")
