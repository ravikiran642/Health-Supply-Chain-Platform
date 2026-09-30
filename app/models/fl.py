"""ORM models for Federated Learning:
drug_consumption_history, fl_rounds, fl_models, fl_forecasts
"""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.database import Base, GUID, JSONType


class FlRoundStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FlNodeLevelEnum(str, enum.Enum):
    DISTRICT = "district"
    STATE = "state"
    NATION = "nation"


class DrugConsumptionHistory(Base):
    __tablename__ = "drug_consumption_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    facility_id = Column(
        GUID(),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    drug_id = Column(
        GUID(),
        ForeignKey("drugs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consumption_date = Column(Date, nullable=False, index=True)
    quantity_consumed = Column(Integer, nullable=False)

    facility = relationship("Facility", backref="consumption_records")
    drug = relationship("Drug", backref="consumption_records")

    __table_args__ = (
        CheckConstraint("quantity_consumed >= 0", name="ck_consumption_qty_non_negative"),
        UniqueConstraint("facility_id", "drug_id", "consumption_date", name="uq_facility_drug_consumption_date"),
        Index("ix_drug_consumption_history_facility_drug_date", "facility_id", "drug_id", "consumption_date"),
    )


class FlRound(Base):
    __tablename__ = "fl_rounds"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    round_number = Column(Integer, unique=True, nullable=False, index=True)
    status = Column(
        Enum(
            FlRoundStatusEnum,
            name="fl_round_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=FlRoundStatusEnum.PENDING,
    )
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    parent_round_id = Column(GUID(), ForeignKey("fl_rounds.id"), nullable=True)
    participating_districts = Column(Integer, nullable=False, default=0)
    participating_states = Column(Integer, nullable=False, default=0)
    total_samples = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(String(1000), nullable=True)
    notes = Column(String(500), nullable=True)

    parent_round = relationship("FlRound", remote_side=[id], backref="child_rounds")
    models = relationship("FlModel", back_populates="round", cascade="all, delete-orphan")
    forecasts = relationship("FlForecast", back_populates="round", cascade="all, delete-orphan")


class FlModel(Base):
    __tablename__ = "fl_models"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    round_id = Column(
        GUID(),
        ForeignKey("fl_rounds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_level = Column(
        Enum(
            FlNodeLevelEnum,
            name="fl_node_level_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )
    node_id = Column(GUID(), nullable=True)
    archive_path = Column(String(500), nullable=False)
    serving_path = Column(String(500), nullable=False)
    is_serving = Column(Boolean, nullable=False, default=False)
    model_size_bytes = Column(Integer, nullable=False)
    architecture_hash = Column(String(64), nullable=False)
    hyperparameters = Column(JSONType(), nullable=True)
    training_metrics = Column(JSONType(), nullable=True)
    sample_count = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    round = relationship("FlRound", back_populates="models")
    forecasts = relationship("FlForecast", back_populates="model", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_fl_models_round_level_node", "round_id", "node_level", "node_id"),
        Index(
            "uq_fl_models_serving_node",
            "node_level",
            "node_id",
            unique=True,
            sqlite_where=is_serving == True,
            postgresql_where=(is_serving == True),
        ),
    )


class FlForecast(Base):
    __tablename__ = "fl_forecasts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    round_id = Column(
        GUID(),
        ForeignKey("fl_rounds.id"),
        nullable=False,
        index=True,
    )
    model_id = Column(
        GUID(),
        ForeignKey("fl_models.id"),
        nullable=False,
        index=True,
    )
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
    forecast_date = Column(Date, nullable=False)
    predicted_quantity = Column(Float, nullable=False)
    generated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    round = relationship("FlRound", back_populates="forecasts")
    model = relationship("FlModel", back_populates="forecasts")
    facility = relationship("Facility")
    drug = relationship("Drug")

    __table_args__ = (
        UniqueConstraint("round_id", "facility_id", "drug_id", "forecast_date", name="uq_fl_forecast_round_fac_drug_date"),
        Index("ix_fl_forecasts_facility_drug_date", "facility_id", "drug_id", "forecast_date"),
    )
