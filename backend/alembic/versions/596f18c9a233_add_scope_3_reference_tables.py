"""Add Scope 3 reference tables

Revision ID: 596f18c9a233
Revises: 3b2584308449
Create Date: 2026-01-19 11:51:28.409501

New tables:
- airports: Airport reference data for flight distance calculations (Category 3.6)
- transport_distance_matrix: Default transport distances between regions (Category 3.4)
- currency_conversions: Currency conversion rates for spend-based calculations
- price_ranges: Expected price ranges for validation
- hotel_emission_factors: Country-specific hotel emission factors (Category 3.6)
- grid_emission_factors: Country-specific grid electricity emission factors (Scope 2 & 3.3)
- refrigerant_gwp: Global Warming Potential values for refrigerants (Scope 1.3)
- waste_disposal_factors: Emission factors for waste disposal methods (Category 3.5)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '596f18c9a233'
down_revision: Union[str, None] = '3b2584308449'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Airports table - for flight distance calculations (Category 3.6)
    op.create_table(
        'airports',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('iata_code', sa.String(3), nullable=False, unique=True),
        sa.Column('icao_code', sa.String(4), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('country_name', sa.String(100), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    op.create_index('ix_airports_iata_code', 'airports', ['iata_code'], unique=True)
    op.create_index('ix_airports_country_code', 'airports', ['country_code'])

    # 2. Transport Distance Matrix - for default transport distances (Category 3.4)
    op.create_table(
        'transport_distance_matrix',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('origin_country', sa.String(2), nullable=False),
        sa.Column('origin_region', sa.String(50), nullable=True),
        sa.Column('destination_country', sa.String(2), nullable=False),
        sa.Column('destination_region', sa.String(50), nullable=True),
        sa.Column('origin_land_km', sa.Integer, nullable=False, default=500),
        sa.Column('sea_distance_km', sa.Integer, nullable=False),
        sa.Column('destination_land_km', sa.Integer, nullable=False, default=100),
        sa.Column('total_distance_km', sa.Integer, nullable=False),
        sa.Column('transport_mode', sa.String(50), nullable=False, default='sea_container'),
        sa.Column('air_distance_km', sa.Integer, nullable=True),
        sa.Column('rail_distance_km', sa.Integer, nullable=True),
        sa.Column('source', sa.String(200), nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_transport_distance_matrix_origin_country', 'transport_distance_matrix', ['origin_country'])
    op.create_index('ix_transport_distance_matrix_destination_country', 'transport_distance_matrix', ['destination_country'])

    # 3. Currency Conversions - for spend-based calculations
    op.create_table(
        'currency_conversions',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('from_currency', sa.String(3), nullable=False),
        sa.Column('to_currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('rate', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('valid_from', sa.Date, nullable=False),
        sa.Column('valid_until', sa.Date, nullable=True),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('rate_type', sa.String(50), nullable=False, default='annual_average'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    op.create_index('ix_currency_conversions_from_currency', 'currency_conversions', ['from_currency'])
    op.create_index('ix_currency_conversions_valid_from', 'currency_conversions', ['valid_from'])

    # 4. Price Ranges - for data validation
    op.create_table(
        'price_ranges',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('material_type', sa.String(100), nullable=False),
        sa.Column('activity_category', sa.String(10), nullable=False),
        sa.Column('min_price_usd', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('max_price_usd', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('typical_price_usd', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('region', sa.String(50), nullable=False, default='Global'),
        sa.Column('source', sa.String(200), nullable=False),
        sa.Column('valid_year', sa.Integer, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    op.create_index('ix_price_ranges_material_type', 'price_ranges', ['material_type'])

    # 5. Hotel Emission Factors - for Category 3.6 Business Travel
    op.create_table(
        'hotel_emission_factors',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('country_name', sa.String(100), nullable=False),
        sa.Column('co2e_per_night', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('electricity_kwh_per_night', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('heating_kwh_per_night', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('water_liters_per_night', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    op.create_index('ix_hotel_emission_factors_country_code', 'hotel_emission_factors', ['country_code'])

    # 6. Grid Emission Factors - for Scope 2 and Category 3.3
    op.create_table(
        'grid_emission_factors',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('country_name', sa.String(100), nullable=False),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('location_factor', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('market_factor', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('co2_factor', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('ch4_factor', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('n2o_factor', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('td_loss_factor', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('td_loss_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    op.create_index('ix_grid_emission_factors_country_code', 'grid_emission_factors', ['country_code'])
    op.create_index('ix_grid_emission_factors_year', 'grid_emission_factors', ['year'])

    # 7. Refrigerant GWP - for Scope 1.3 Fugitive Emissions
    op.create_table(
        'refrigerant_gwp',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('chemical_formula', sa.String(100), nullable=True),
        sa.Column('cas_number', sa.String(20), nullable=True),
        sa.Column('gwp_ar6', sa.Integer, nullable=False),
        sa.Column('gwp_ar5', sa.Integer, nullable=True),
        sa.Column('gwp_ar4', sa.Integer, nullable=True),
        sa.Column('refrigerant_type', sa.String(50), nullable=False),
        sa.Column('applications', sa.String(500), nullable=True),
        sa.Column('is_phased_out', sa.Boolean, nullable=False, default=False),
        sa.Column('phase_out_date', sa.Date, nullable=True),
        sa.Column('source', sa.String(100), nullable=False, default='IPCC_AR6_2021'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    op.create_index('ix_refrigerant_gwp_name', 'refrigerant_gwp', ['name'])

    # 8. Waste Disposal Factors - for Category 3.5
    op.create_table(
        'waste_disposal_factors',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('waste_type', sa.String(100), nullable=False),
        sa.Column('disposal_method', sa.String(50), nullable=False),
        sa.Column('co2e_per_kg', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('co2_per_kg', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('ch4_per_kg', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('n2o_per_kg', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('avoided_co2e_per_kg', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=True),
        sa.Column('region', sa.String(50), nullable=False, default='Global'),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )
    op.create_index('ix_waste_disposal_factors_waste_type', 'waste_disposal_factors', ['waste_type'])
    op.create_index('ix_waste_disposal_factors_disposal_method', 'waste_disposal_factors', ['disposal_method'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('waste_disposal_factors')
    op.drop_table('refrigerant_gwp')
    op.drop_table('grid_emission_factors')
    op.drop_table('hotel_emission_factors')
    op.drop_table('price_ranges')
    op.drop_table('currency_conversions')
    op.drop_table('transport_distance_matrix')
    op.drop_table('airports')
