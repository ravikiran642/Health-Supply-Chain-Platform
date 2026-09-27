"""Inventory schema: drugs, inventory_batches, and stock_transactions

Revision ID: 0003_inventory_schema
Revises: 0002_add_user_profile_fields
Create Date: 2026-09-27 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0003_inventory_schema'
down_revision: Union[str, None] = '0002_add_user_profile_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drugs master table
    op.create_table(
        'drugs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column(
            'category',
            sa.Enum('antibiotic', 'analgesic', 'antimalarial', 'vaccine', 'ors', 'other', name='drug_category_enum'),
            nullable=False
        ),
        sa.Column(
            'unit',
            sa.Enum('tablet', 'capsule', 'ml', 'vial', 'sachet', 'tube', name='drug_unit_enum'),
            nullable=False
        ),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_drugs_name'), 'drugs', ['name'], unique=True)

    # 2. Inventory batches table
    op.create_table(
        'inventory_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('drug_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drugs.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('batch_number', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            'status',
            sa.Enum('active', 'expired', 'quarantined', 'depleted', name='batch_status_enum'),
            nullable=False,
            server_default='active'
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('quantity >= 0', name='chk_batch_quantity_positive'),
        sa.UniqueConstraint('facility_id', 'drug_id', 'batch_number', name='uq_facility_drug_batch')
    )
    op.create_index(op.f('ix_inventory_batches_facility_id'), 'inventory_batches', ['facility_id'], unique=False)
    op.create_index(op.f('ix_inventory_batches_drug_id'), 'inventory_batches', ['drug_id'], unique=False)
    op.create_index(op.f('ix_inventory_batches_expiry_date'), 'inventory_batches', ['expiry_date'], unique=False)
    op.create_index(op.f('ix_inventory_batches_status'), 'inventory_batches', ['status'], unique=False)

    # 3. Stock transactions table (immutable ledger)
    op.create_table(
        'stock_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id'), nullable=False),
        sa.Column('drug_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drugs.id'), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inventory_batches.id'), nullable=True),
        sa.Column(
            'transaction_type',
            sa.Enum('receive', 'dispense', 'write_off', 'transfer_in', 'transfer_out', 'adjustment', name='transaction_type_enum'),
            nullable=False
        ),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_stock_transactions_facility_id'), 'stock_transactions', ['facility_id'], unique=False)
    op.create_index(op.f('ix_stock_transactions_drug_id'), 'stock_transactions', ['drug_id'], unique=False)
    op.create_index(op.f('ix_stock_transactions_batch_id'), 'stock_transactions', ['batch_id'], unique=False)
    op.create_index(op.f('ix_stock_transactions_performed_by'), 'stock_transactions', ['performed_by'], unique=False)
    op.create_index(op.f('ix_stock_transactions_created_at'), 'stock_transactions', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('stock_transactions')
    op.drop_table('inventory_batches')
    op.drop_table('drugs')
