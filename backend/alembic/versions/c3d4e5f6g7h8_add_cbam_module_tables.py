"""Add CBAM module tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-25 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # CBAM Products (Reference table for CN codes)
    op.create_table(
        'cbam_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cn_code', sa.String(10), nullable=False, index=True),
        sa.Column('cn_code_full', sa.String(12), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('sector', sa.String(20), nullable=False, index=True),
        sa.Column('aggregated_category', sa.String(100), nullable=False),
        sa.Column('direct_emissions_required', sa.Boolean, default=True),
        sa.Column('indirect_emissions_required', sa.Boolean, default=False),
        sa.Column('default_see', sa.Numeric(18, 6), nullable=True),
        sa.Column('default_see_source', sa.String(200), nullable=True),
        sa.Column('has_precursors', sa.Boolean, default=False),
        sa.Column('precursor_cn_codes', postgresql.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('valid_from', sa.Date, nullable=False),
        sa.Column('valid_until', sa.Date, nullable=True),
    )

    # CBAM Installations (Non-EU production facilities)
    op.create_table(
        'cbam_installations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('installation_id_external', sa.String(100), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=False, index=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('coordinates_lat', sa.Numeric(9, 6), nullable=True),
        sa.Column('coordinates_lng', sa.Numeric(9, 6), nullable=True),
        sa.Column('operator_name', sa.String(255), nullable=False),
        sa.Column('operator_contact_name', sa.String(255), nullable=True),
        sa.Column('operator_contact_email', sa.String(255), nullable=True),
        sa.Column('operator_contact_phone', sa.String(50), nullable=True),
        sa.Column('sector', sa.String(20), nullable=False, index=True),
        sa.Column('production_processes', postgresql.JSON, nullable=True),
        sa.Column('annual_production_capacity_tonnes', sa.Numeric(18, 2), nullable=True),
        sa.Column('direct_emissions_intensity', sa.Numeric(18, 6), nullable=True),
        sa.Column('indirect_emissions_intensity', sa.Numeric(18, 6), nullable=True),
        sa.Column('electricity_consumption_mwh_per_tonne', sa.Numeric(18, 6), nullable=True),
        sa.Column('grid_emission_factor', sa.Numeric(18, 6), nullable=True),
        sa.Column('carbon_price_paid', sa.Numeric(18, 2), nullable=True),
        sa.Column('carbon_price_mechanism', sa.String(200), nullable=True),
        sa.Column('verification_status', sa.String(20), default='unverified'),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('verifier_name', sa.String(255), nullable=True),
        sa.Column('verification_statement', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )

    # CBAM Imports (Individual import declarations)
    op.create_table(
        'cbam_imports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('reporting_period_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reporting_periods.id'), nullable=False, index=True),
        sa.Column('installation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cbam_installations.id'), nullable=True),
        sa.Column('import_date', sa.Date, nullable=False, index=True),
        sa.Column('customs_entry_number', sa.String(50), nullable=True),
        sa.Column('customs_procedure', sa.String(20), nullable=True),
        sa.Column('cn_code', sa.String(10), nullable=False, index=True),
        sa.Column('product_description', sa.String(500), nullable=False),
        sa.Column('origin_country', sa.String(2), nullable=False, index=True),
        sa.Column('net_mass_kg', sa.Numeric(18, 2), nullable=False),
        sa.Column('net_mass_tonnes', sa.Numeric(18, 4), nullable=False),
        sa.Column('supplementary_unit', sa.String(20), nullable=True),
        sa.Column('supplementary_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('direct_emissions_tco2e', sa.Numeric(18, 6), nullable=False),
        sa.Column('indirect_emissions_tco2e', sa.Numeric(18, 6), nullable=True),
        sa.Column('total_embedded_emissions_tco2e', sa.Numeric(18, 6), nullable=False),
        sa.Column('specific_embedded_emissions', sa.Numeric(18, 6), nullable=False),
        sa.Column('calculation_method', sa.String(20), default='default'),
        sa.Column('default_value_used', sa.Boolean, default=False),
        sa.Column('direct_ef_used', sa.Numeric(18, 6), nullable=True),
        sa.Column('indirect_ef_used', sa.Numeric(18, 6), nullable=True),
        sa.Column('precursor_emissions_tco2e', sa.Numeric(18, 6), nullable=True),
        sa.Column('precursor_details', postgresql.JSON, nullable=True),
        sa.Column('carbon_price_paid_eur', sa.Numeric(18, 2), nullable=True),
        sa.Column('carbon_price_country', sa.String(2), nullable=True),
        sa.Column('carbon_price_mechanism', sa.String(200), nullable=True),
        sa.Column('carbon_price_deduction_tco2e', sa.Numeric(18, 6), nullable=True),
        sa.Column('net_emissions_tco2e', sa.Numeric(18, 6), nullable=False),
        sa.Column('data_source', sa.String(50), default='estimate'),
        sa.Column('data_quality_score', sa.Integer, default=5),
        sa.Column('supporting_documents', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )

    # CBAM Quarterly Reports (Transitional phase)
    op.create_table(
        'cbam_quarterly_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('reporting_year', sa.Integer, nullable=False, index=True),
        sa.Column('reporting_quarter', sa.Integer, nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('submission_deadline', sa.Date, nullable=False),
        sa.Column('total_imports_count', sa.Integer, default=0),
        sa.Column('total_mass_tonnes', sa.Numeric(18, 2), default=0),
        sa.Column('total_direct_emissions_tco2e', sa.Numeric(18, 2), default=0),
        sa.Column('total_indirect_emissions_tco2e', sa.Numeric(18, 2), default=0),
        sa.Column('total_embedded_emissions_tco2e', sa.Numeric(18, 2), default=0),
        sa.Column('total_carbon_price_deductions_tco2e', sa.Numeric(18, 2), default=0),
        sa.Column('total_net_emissions_tco2e', sa.Numeric(18, 2), default=0),
        sa.Column('by_sector', postgresql.JSON, nullable=True),
        sa.Column('by_country', postgresql.JSON, nullable=True),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('submitted_at', sa.DateTime, nullable=True),
        sa.Column('submission_reference', sa.String(100), nullable=True),
        sa.Column('accepted_at', sa.DateTime, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.UniqueConstraint('organization_id', 'reporting_year', 'reporting_quarter', name='uq_cbam_quarterly_org_year_quarter'),
    )

    # CBAM Annual Declarations (Definitive phase)
    op.create_table(
        'cbam_annual_declarations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('reporting_year', sa.Integer, nullable=False, index=True),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('submission_deadline', sa.Date, nullable=False),
        sa.Column('total_imports_count', sa.Integer, default=0),
        sa.Column('total_mass_tonnes', sa.Numeric(18, 2), default=0),
        sa.Column('total_embedded_emissions_tco2e', sa.Numeric(18, 2), default=0),
        sa.Column('carbon_price_deductions_tco2e', sa.Numeric(18, 2), default=0),
        sa.Column('carbon_price_deductions_eur', sa.Numeric(18, 2), default=0),
        sa.Column('net_emissions_tco2e', sa.Numeric(18, 2), nullable=False),
        sa.Column('certificates_required', sa.Integer, default=0),
        sa.Column('certificates_purchased', sa.Integer, default=0),
        sa.Column('certificates_surrendered', sa.Integer, default=0),
        sa.Column('certificates_balance', sa.Integer, default=0),
        sa.Column('average_certificate_price_eur', sa.Numeric(18, 2), nullable=True),
        sa.Column('total_certificate_cost_eur', sa.Numeric(18, 2), default=0),
        sa.Column('total_liability_eur', sa.Numeric(18, 2), default=0),
        sa.Column('by_sector', postgresql.JSON, nullable=True),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('submitted_at', sa.DateTime, nullable=True),
        sa.Column('submission_reference', sa.String(100), nullable=True),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('verifier_name', sa.String(255), nullable=True),
        sa.Column('verification_statement', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.UniqueConstraint('organization_id', 'reporting_year', name='uq_cbam_annual_org_year'),
    )

    # CBAM Default Values (Reference data)
    op.create_table(
        'cbam_default_values',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cn_code', sa.String(10), nullable=False, index=True),
        sa.Column('sector', sa.String(20), nullable=False, index=True),
        sa.Column('product_description', sa.String(500), nullable=False),
        sa.Column('direct_see', sa.Numeric(18, 6), nullable=False),
        sa.Column('indirect_see', sa.Numeric(18, 6), nullable=True),
        sa.Column('total_see', sa.Numeric(18, 6), nullable=False),
        sa.Column('source', sa.String(200), nullable=False),
        sa.Column('source_reference', sa.String(100), nullable=True),
        sa.Column('valid_from', sa.Date, nullable=False),
        sa.Column('valid_until', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
    )

    # CBAM Grid Factors (Third-country electricity)
    op.create_table(
        'cbam_grid_factors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('country_code', sa.String(2), nullable=False, unique=True, index=True),
        sa.Column('country_name', sa.String(100), nullable=False),
        sa.Column('grid_factor', sa.Numeric(18, 6), nullable=False),
        sa.Column('source', sa.String(200), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('valid_from', sa.Date, nullable=False),
        sa.Column('valid_until', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
    )

    # EU ETS Prices (Weekly carbon prices)
    op.create_table(
        'eu_ets_prices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('price_date', sa.Date, nullable=False, unique=True, index=True),
        sa.Column('week_number', sa.Integer, nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('price_eur', sa.Numeric(18, 2), nullable=False),
        sa.Column('source', sa.String(100), default='EU Commission'),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('eu_ets_prices')
    op.drop_table('cbam_grid_factors')
    op.drop_table('cbam_default_values')
    op.drop_table('cbam_annual_declarations')
    op.drop_table('cbam_quarterly_reports')
    op.drop_table('cbam_imports')
    op.drop_table('cbam_installations')
    op.drop_table('cbam_products')
