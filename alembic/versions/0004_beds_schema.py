"""Beds schema: bed_inventories and bed_occupancy_logs

Revision ID: 0004_beds_schema
Revises: 0003_inventory_schema
Create Date: 2026-09-27 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0004_beds_schema'
down_revision: Union[str, None] = '0003_inventory_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Bed inventories table
    op.create_table(
        'bed_inventories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column(
            'bed_type',
            sa.Enum('general', 'icu', 'oxygen', 'maternity', 'pediatric', name='bed_type_enum'),
            nullable=False
        ),
        sa.Column('total_beds', sa.Integer(), nullable=False),
        sa.Column('occupied_beds', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('total_beds >= 0', name='chk_total_beds_positive'),
        sa.CheckConstraint('occupied_beds >= 0', name='chk_occupied_beds_positive'),
        sa.CheckConstraint('occupied_beds <= total_beds', name='chk_occupied_le_total'),
        sa.UniqueConstraint('facility_id', 'bed_type', name='uq_facility_bed_type')
    )
    op.create_index(op.f('ix_bed_inventories_facility_id'), 'bed_inventories', ['facility_id'], unique=False)

    # 2. Bed occupancy logs table
    op.create_table(
        'bed_occupancy_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id'), nullable=False),
        sa.Column(
            'bed_type',
            sa.Enum('general', 'icu', 'oxygen', 'maternity', 'pediatric', name='bed_type_enum'),
            nullable=False
        ),
        sa.Column('occupied_beds', sa.Integer(), nullable=False),
        sa.Column('total_beds', sa.Integer(), nullable=False),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_bed_occupancy_logs_facility_id'), 'bed_occupancy_logs', ['facility_id'], unique=False)
    op.create_index(op.f('ix_bed_occupancy_logs_recorded_by'), 'bed_occupancy_logs', ['recorded_by'], unique=False)
    op.create_index(op.f('ix_bed_occupancy_logs_recorded_at'), 'bed_occupancy_logs', ['recorded_at'], unique=False)


def downgrade() -> None:
    op.drop_table('bed_occupancy_logs')
    op.drop_table('bed_inventories')
