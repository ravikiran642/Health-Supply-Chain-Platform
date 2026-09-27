"""Add phone and must_change_password to users table

Revision ID: 0002_add_user_profile_fields
Revises: 0001_initial_rbac_schema
Create Date: 2026-09-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_add_user_profile_fields'
down_revision: Union[str, None] = '0001_initial_rbac_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('phone', sa.String(length=20), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )


def downgrade() -> None:
    op.drop_column('users', 'must_change_password')
    op.drop_column('users', 'phone')
