"""FL schema: drug_consumption_history, fl_rounds, fl_models, fl_forecasts

Revision ID: 0006_fl_schema
Revises: 0005_attendance_schema
Create Date: 2026-09-29 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0006_fl_schema'
down_revision: Union[str, None] = '0005_attendance_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. drug_consumption_history
    op.create_table(
        'drug_consumption_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('drug_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drugs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('consumption_date', sa.Date(), nullable=False),
        sa.Column('quantity_consumed', sa.Integer(), nullable=False),
        sa.CheckConstraint('quantity_consumed >= 0', name='ck_consumption_qty_non_negative'),
        sa.UniqueConstraint('facility_id', 'drug_id', 'consumption_date', name='uq_facility_drug_consumption_date'),
    )
    op.create_index(op.f('ix_drug_consumption_history_facility_id'), 'drug_consumption_history', ['facility_id'], unique=False)
    op.create_index(op.f('ix_drug_consumption_history_drug_id'), 'drug_consumption_history', ['drug_id'], unique=False)
    op.create_index(op.f('ix_drug_consumption_history_consumption_date'), 'drug_consumption_history', ['consumption_date'], unique=False)
    op.create_index('ix_drug_consumption_history_facility_drug_date', 'drug_consumption_history', ['facility_id', 'drug_id', 'consumption_date'], unique=False)

    # 2. fl_rounds
    op.create_table(
        'fl_rounds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'running', 'completed', 'failed', name='fl_round_status_enum'),
            nullable=False,
            server_default='pending'
        ),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parent_round_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fl_rounds.id'), nullable=True),
        sa.Column('participating_districts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('participating_states', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_samples', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.UniqueConstraint('round_number', name='uq_fl_rounds_round_number'),
    )
    op.create_index(op.f('ix_fl_rounds_round_number'), 'fl_rounds', ['round_number'], unique=True)

    # 3. fl_models
    op.create_table(
        'fl_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('round_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fl_rounds.id', ondelete='CASCADE'), nullable=False),
        sa.Column(
            'node_level',
            sa.Enum('district', 'state', 'nation', name='fl_node_level_enum'),
            nullable=False
        ),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('archive_path', sa.String(length=500), nullable=False),
        sa.Column('serving_path', sa.String(length=500), nullable=False),
        sa.Column('is_serving', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('model_size_bytes', sa.Integer(), nullable=False),
        sa.Column('architecture_hash', sa.String(length=64), nullable=False),
        sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('training_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sample_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_fl_models_round_id'), 'fl_models', ['round_id'], unique=False)
    op.create_index(op.f('ix_fl_models_node_level'), 'fl_models', ['node_level'], unique=False)
    op.create_index('ix_fl_models_round_level_node', 'fl_models', ['round_id', 'node_level', 'node_id'], unique=False)
    op.create_index(
        'uq_fl_models_serving_node',
        'fl_models',
        ['node_level', 'node_id'],
        unique=True,
        postgresql_where=sa.text('is_serving = true')
    )

    # 4. fl_forecasts
    op.create_table(
        'fl_forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('round_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fl_rounds.id'), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fl_models.id'), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id'), nullable=False),
        sa.Column('drug_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drugs.id'), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('predicted_quantity', sa.Float(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('round_id', 'facility_id', 'drug_id', 'forecast_date', name='uq_fl_forecast_round_fac_drug_date'),
    )
    op.create_index(op.f('ix_fl_forecasts_round_id'), 'fl_forecasts', ['round_id'], unique=False)
    op.create_index(op.f('ix_fl_forecasts_model_id'), 'fl_forecasts', ['model_id'], unique=False)
    op.create_index(op.f('ix_fl_forecasts_facility_id'), 'fl_forecasts', ['facility_id'], unique=False)
    op.create_index(op.f('ix_fl_forecasts_drug_id'), 'fl_forecasts', ['drug_id'], unique=False)
    op.create_index('ix_fl_forecasts_facility_drug_date', 'fl_forecasts', ['facility_id', 'drug_id', 'forecast_date'], unique=False)


def downgrade() -> None:
    op.drop_table('fl_forecasts')
    op.drop_table('fl_models')
    op.drop_table('fl_rounds')
    op.drop_table('drug_consumption_history')
    op.execute('DROP TYPE IF EXISTS fl_round_status_enum')
    op.execute('DROP TYPE IF EXISTS fl_node_level_enum')
