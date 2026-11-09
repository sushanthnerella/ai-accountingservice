"""add_phases_2_to_5_tables

Revision ID: 002_phases_2_to_5
Revises: 001_initial_schema
Create Date: 2026-11-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_phases_2_to_5'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Invoices & Invoice Items
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('invoice_type', sa.String(50), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('counterparty_name', sa.String(255), nullable=False),
        sa.Column('counterparty_gstin', sa.String(15), nullable=True),
        sa.Column('counterparty_state_code', sa.String(2), nullable=True),
        sa.Column('place_of_supply_state_code', sa.String(2), nullable=False),
        sa.Column('taxable_amount', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('cgst_amount', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('sgst_amount', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('igst_amount', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('cess_amount', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('round_off_amount', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('total_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('balance_due_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('itc_eligibility', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('is_reverse_charge', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_export_lut', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('lut_number', sa.String(50), nullable=True),
        sa.Column('approval_status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('client_business_id', 'counterparty_gstin', 'invoice_number', name='uq_invoice_client_gstin_num')
    )
    op.create_index('ix_invoices_org_id', 'invoices', ['organization_id'])
    op.create_index('ix_invoices_client_id', 'invoices', ['client_business_id'])

    op.create_table(
        'invoice_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('hsn_sac_code', sa.String(10), nullable=True),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False, server_default='1.0000'),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('taxable_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('tax_rate_percent', sa.Numeric(5, 2), nullable=False, server_default='18.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_invoice_items_invoice_id', 'invoice_items', ['invoice_id'])

    # 2. Bank Accounts & Bank Transactions
    op.create_table(
        'bank_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_name', sa.String(100), nullable=False),
        sa.Column('account_number', sa.String(50), nullable=False),
        sa.Column('ifsc_code', sa.String(11), nullable=False),
        sa.Column('bank_name', sa.String(100), nullable=False),
        sa.Column('account_type', sa.String(50), nullable=False, server_default='CURRENT'),
        sa.Column('opening_balance', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('opening_balance_date', sa.Date(), nullable=False),
        sa.Column('current_ledger_balance', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('client_business_id', 'account_number', 'ifsc_code', name='uq_bank_acc_client_num_ifsc')
    )
    op.create_index('ix_bank_accounts_org_id', 'bank_accounts', ['organization_id'])
    op.create_index('ix_bank_accounts_client_id', 'bank_accounts', ['client_business_id'])

    op.create_table(
        'bank_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bank_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('value_date', sa.Date(), nullable=True),
        sa.Column('narration', sa.Text(), nullable=False),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('utr_number', sa.String(100), nullable=True),
        sa.Column('cheque_number', sa.String(20), nullable=True),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('running_balance', sa.Numeric(18, 4), nullable=False),
        sa.Column('classification_category', sa.String(50), nullable=False, server_default='UNCLASSIFIED'),
        sa.Column('reconciliation_status', sa.String(50), nullable=False, server_default='UNRECONCILED'),
        sa.Column('unreconciled_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_bank_transactions_org_id', 'bank_transactions', ['organization_id'])
    op.create_index('ix_bank_transactions_client_id', 'bank_transactions', ['client_business_id'])
    op.create_index('ix_bank_transactions_utr', 'bank_transactions', ['utr_number'])

    # 3. Chart of Accounts & Journal Entries
    op.create_table(
        'chart_of_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_code', sa.String(20), nullable=False),
        sa.Column('account_name', sa.String(150), nullable=False),
        sa.Column('account_type', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('client_business_id', 'account_code', name='uq_coa_code_client')
    )
    op.create_index('ix_chart_of_accounts_org_id', 'chart_of_accounts', ['organization_id'])
    op.create_index('ix_chart_of_accounts_client_id', 'chart_of_accounts', ['client_business_id'])

    op.create_table(
        'journal_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_number', sa.String(50), nullable=False),
        sa.Column('posting_date', sa.Date(), nullable=False),
        sa.Column('financial_year', sa.String(9), nullable=False, server_default='2024-2025'),
        sa.Column('voucher_type', sa.String(50), nullable=False),
        sa.Column('narration', sa.Text(), nullable=False),
        sa.Column('is_posted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('client_business_id', 'financial_year', 'entry_number', name='uq_entry_num_fy_client')
    )
    op.create_index('ix_journal_entries_org_id', 'journal_entries', ['organization_id'])
    op.create_index('ix_journal_entries_client_id', 'journal_entries', ['client_business_id'])

    op.create_table(
        'journal_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('journal_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chart_of_accounts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('entry_side', sa.String(2), nullable=False),
        sa.Column('amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_journal_lines_entry_id', 'journal_lines', ['journal_entry_id'])
    op.create_index('ix_journal_lines_account_id', 'journal_lines', ['account_id'])

    # 4. Reconciliation Matches
    op.create_table(
        'reconciliation_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bank_transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bank_transactions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('match_scenario', sa.String(50), nullable=False),
        sa.Column('allocated_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('tds_deducted_amount', sa.Numeric(18, 4), nullable=False, server_default='0.0000'),
        sa.Column('tds_section', sa.String(20), nullable=False, server_default='NONE'),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('match_rationale', sa.Text(), nullable=False),
        sa.Column('approval_status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_reconciliation_matches_org_id', 'reconciliation_matches', ['organization_id'])
    op.create_index('ix_reconciliation_matches_client_id', 'reconciliation_matches', ['client_business_id'])

    # RLS policies
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        for table in ['invoices', 'bank_accounts', 'bank_transactions', 'chart_of_accounts', 'journal_entries', 'reconciliation_matches']:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            op.execute(f"""
                CREATE POLICY {table}_tenant_isolation ON {table}
                FOR ALL
                USING (
                    organization_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid
                );
            """)

def downgrade() -> None:
    op.drop_table('reconciliation_matches')
    op.drop_table('journal_lines')
    op.drop_table('journal_entries')
    op.drop_table('chart_of_accounts')
    op.drop_table('bank_transactions')
    op.drop_table('bank_accounts')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
