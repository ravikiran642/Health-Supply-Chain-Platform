"""Initial RBAC and geographic schema

Revision ID: 0001_initial_rbac_schema
Revises: 
Create Date: 2026-09-16 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_rbac_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. States table
    op.create_table(
        'states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False, unique=True),
    )
    op.create_index(op.f('ix_states_code'), 'states', ['code'], unique=True)

    # 2. Districts table
    op.create_table(
        'districts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('states.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False, unique=True),
    )
    op.create_index(op.f('ix_districts_state_id'), 'districts', ['state_id'], unique=False)
    op.create_index(op.f('ix_districts_code'), 'districts', ['code'], unique=True)

    # 3. Facilities table
    facility_type_enum = postgresql.ENUM('PHC', 'CHC', name='facility_type_enum')
    facility_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'facilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('district_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('districts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('type', sa.Enum('PHC', 'CHC', name='facility_type_enum'), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False, unique=True),
    )
    op.create_index(op.f('ix_facilities_district_id'), 'facilities', ['district_id'], unique=False)
    op.create_index(op.f('ix_facilities_code'), 'facilities', ['code'], unique=True)

    # 4. Roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('description', sa.String(length=255), nullable=True),
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    # 5. Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.String(length=255), nullable=True),
    )
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)

    # 6. Junction: role_permissions
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    )

    # 7. Users table
    scope_level_enum = postgresql.ENUM('platform', 'national', 'state', 'district', 'phc', name='scope_level_enum')
    scope_level_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('scope_level', sa.Enum('platform', 'national', 'state', 'district', 'phc', name='scope_level_enum'), nullable=False),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_scope_level'), 'users', ['scope_level'], unique=False)
    op.create_index(op.f('ix_users_scope_id'), 'users', ['scope_id'], unique=False)

    # 8. Junction: user_roles
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    )

    # 9. Refresh tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_revoked'), 'refresh_tokens', ['revoked'], unique=False)

    # 10. Audit logs table
    audit_result_enum = postgresql.ENUM('success', 'denied', name='audit_result_enum')
    audit_result_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('result', sa.Enum('success', 'denied', name='audit_result_enum'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_result'), 'audit_logs', ['result'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.execute('DROP TYPE IF EXISTS audit_result_enum')
    op.drop_table('refresh_tokens')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS scope_level_enum')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('facilities')
    op.execute('DROP TYPE IF EXISTS facility_type_enum')
    op.drop_table('districts')
    op.drop_table('states')
