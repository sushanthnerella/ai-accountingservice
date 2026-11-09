"""initial_schema_and_rls

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-11-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create Users & RefreshTokens
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'])

    # 2. Create Organizations & Memberships
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('org_type', sa.String(50), nullable=False, server_default='FREELANCER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    op.create_table(
        'organization_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='STAFF_ACCOUNTANT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_member')
    )
    op.create_index('ix_organization_memberships_org_id', 'organization_memberships', ['organization_id'])
    op.create_index('ix_organization_memberships_user_id', 'organization_memberships', ['user_id'])

    # 3. Create Client Businesses
    op.create_table(
        'client_businesses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trade_name', sa.String(255), nullable=True),
        sa.Column('business_type', sa.String(50), nullable=False, server_default='PROPRIETORSHIP'),
        sa.Column('pan', sa.String(10), nullable=False),
        sa.Column('gstin', sa.String(15), nullable=True),
        sa.Column('state_code', sa.String(2), nullable=False),
        sa.Column('is_composition_scheme', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'pan', name='uq_org_pan')
    )
    op.create_index('ix_client_businesses_org_id', 'client_businesses', ['organization_id'])
    op.create_index('ix_client_businesses_pan', 'client_businesses', ['pan'])

    # 4. Create Document Batches & Documents
    op.create_table(
        'document_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_reference', sa.String(64), nullable=False, unique=True),
        sa.Column('total_files', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PROCESSING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_document_batches_org_id', 'document_batches', ['organization_id'])
    op.create_index('ix_document_batches_client_id', 'document_batches', ['client_business_id'])

    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_batches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('storage_path', sa.String(512), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='AUTO_DETECT'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PROCESSING'),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('duplicate_of_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_documents_org_id', 'documents', ['organization_id'])
    op.create_index('ix_documents_client_id', 'documents', ['client_business_id'])
    op.create_index('ix_documents_sha256_hash', 'documents', ['sha256_hash'])

    # 5. Create Immutable Audit Events
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('entity_name', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(64), nullable=True),
        sa.Column('payload_before', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('payload_after', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_audit_events_org_id', 'audit_events', ['organization_id'])
    op.create_index('ix_audit_events_event_type', 'audit_events', ['event_type'])

    # 6. Setup PostgreSQL Row-Level Security (RLS) policies
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        for table in ['client_businesses', 'document_batches', 'documents', 'audit_events']:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            op.execute(f"""
                CREATE POLICY {table}_tenant_isolation ON {table}
                FOR ALL
                USING (
                    organization_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid
                );
            """)

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        for table in ['audit_events', 'documents', 'document_batches', 'client_businesses']:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table('audit_events')
    op.drop_table('documents')
    op.drop_table('document_batches')
    op.drop_table('client_businesses')
    op.drop_table('organization_memberships')
    op.drop_table('organizations')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
