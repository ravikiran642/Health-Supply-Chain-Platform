"""Staff attendance schema: staff_attendance table

Revision ID: 0005_attendance_schema
Revises: 0004_beds_schema
Create Date: 2026-09-27 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0005_attendance_schema'
down_revision: Union[str, None] = '0004_beds_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'staff_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('present', 'absent', 'leave', 'half_day', 'on_duty', name='attendance_status_enum'),
            nullable=False
        ),
        sa.Column('check_in_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_out_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_modified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('last_modified_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('user_id', 'attendance_date', name='uq_user_attendance_date'),
    )
    op.create_index(op.f('ix_staff_attendance_facility_id'), 'staff_attendance', ['facility_id'], unique=False)
    op.create_index(op.f('ix_staff_attendance_user_id'), 'staff_attendance', ['user_id'], unique=False)
    op.create_index(op.f('ix_staff_attendance_attendance_date'), 'staff_attendance', ['attendance_date'], unique=False)
    op.create_index('ix_staff_attendance_facility_date', 'staff_attendance', ['facility_id', 'attendance_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_staff_attendance_facility_date', table_name='staff_attendance')
    op.drop_table('staff_attendance')
    op.execute('DROP TYPE IF EXISTS attendance_status_enum')
