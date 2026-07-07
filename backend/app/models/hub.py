"""Data Hub models — the organization's inventory profile.

The hub reframes the upload flow around a standing profile: before any file is
parsed, the organization declares (per GHG category) what is relevant, what it
will calculate, where the data comes from and in what form. That profile is
both the completeness baseline ("what's missing" is measured against it) and
the parsing context injected into every ingest (so the parser stops asking
what it already knows).

Coverage is never stored — it is computed from StagedRow/Activity so the hub
matrix is always truthful.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlmodel import SQLModel, Field, Column, JSON


class CategoryRelevance(str, Enum):
    """Materiality decision per GHG category."""

    RELEVANT = "relevant"
    NOT_RELEVANT = "not_relevant"  # requires exclusion_reason (documented exclusion)
    NOT_SURE = "not_sure"


class ExpectedDataForm(str, Enum):
    """What backs the data for a category — pre-declares the measurement tier."""

    METERS = "meters"  # primary/metered readings → measured
    INVOICES = "invoices"  # billed quantities → calculated
    SPEND = "spend"  # monetary only (EEIO) → estimated
    SUPPLIER_REPORTS = "supplier_reports"  # contractor/supplier statements
    NONE_YET = "none_yet"  # no data source identified → gap to chase


class CategoryProfile(SQLModel, table=True):
    """One organization's standing answer for one GHG category.

    ``site_id`` is NULL for the org-level profile (the default); large
    organizations that report per site add site-level rows that override the
    org row for that site. Uniqueness on (organization_id, site_id,
    category_code) is enforced by the upsert endpoint, not the database,
    because NULL site_id rows would escape a DB unique constraint on Postgres.
    """

    __tablename__ = "category_profiles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    site_id: Optional[UUID] = Field(default=None, foreign_key="sites.id", index=True)

    scope: int = Field(ge=1, le=3)
    category_code: str = Field(max_length=10, index=True)

    # Plain-string columns (NOT native PG enums) — see IngestionSession.status.
    relevance: CategoryRelevance = Field(
        default=CategoryRelevance.NOT_SURE,
        sa_column=Column("relevance", String(20), nullable=False),
    )
    # Required when relevance = not_relevant: the documented exclusion an
    # auditor reads instead of silence.
    exclusion_reason: Optional[str] = Field(default=None, max_length=500)
    calculate_this_period: bool = Field(default=True)

    # Layer 2 — filled progressively, only for relevant categories.
    data_owner: Optional[str] = Field(default=None, max_length=255)
    expected_form: Optional[ExpectedDataForm] = Field(
        default=None,
        sa_column=Column("expected_form", String(20), nullable=True),
    )
    # Method answers that only some categories need (Scope 2 market/location,
    # refrigerant gases, ...): a small JSON bag instead of 19 nullable columns.
    details: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


# The canonical hub matrix — every category, always visible. ``aggregates``
# lists the category_code values (as found on StagedRow/Activity/EmissionFactor)
# that roll up into this hub row: electricity is one decision for the client
# even though the ledger encodes location-based (2.1), market-based (2.2) and
# the bare legacy "2".
GHG_CATEGORIES: list[dict] = [
    # Scope 1 — Direct
    {
        "scope": 1,
        "code": "1.1",
        "name": "Stationary Combustion",
        "description": "Fuel burned on site — boilers, furnaces, generators",
        "aggregates": ["1.1"],
    },
    {
        "scope": 1,
        "code": "1.2",
        "name": "Mobile Combustion",
        "description": "Company-owned or leased vehicles",
        "aggregates": ["1.2"],
    },
    {
        "scope": 1,
        "code": "1.3",
        "name": "Fugitive Emissions",
        "description": "Refrigerants (HVAC), fire suppression",
        "aggregates": ["1.3"],
    },
    # Scope 2 — Purchased energy
    {
        "scope": 2,
        "code": "2.1",
        "name": "Purchased Electricity",
        "description": "Grid electricity (location- and market-based)",
        "aggregates": ["2", "2.1", "2.2"],
    },
    {
        "scope": 2,
        "code": "2.3",
        "name": "Purchased Heat, Steam & Cooling",
        "description": "District heating, steam, chilled water",
        "aggregates": ["2.3"],
    },
    # Scope 3 — Value chain (upstream)
    {
        "scope": 3,
        "code": "3.1",
        "name": "Purchased Goods & Services",
        "description": "Everything the company buys",
        "aggregates": ["3.1"],
    },
    {
        "scope": 3,
        "code": "3.2",
        "name": "Capital Goods",
        "description": "Equipment, machinery, buildings purchased",
        "aggregates": ["3.2"],
    },
    {
        "scope": 3,
        "code": "3.3",
        "name": "Fuel & Energy Related",
        "description": "Upstream of Scope 1/2 fuels — WTT, T&D losses",
        "aggregates": ["3.3"],
    },
    {
        "scope": 3,
        "code": "3.4",
        "name": "Upstream Transportation",
        "description": "Inbound freight and distribution",
        "aggregates": ["3.4"],
    },
    {
        "scope": 3,
        "code": "3.5",
        "name": "Waste from Operations",
        "description": "Waste disposal and treatment",
        "aggregates": ["3.5"],
    },
    {
        "scope": 3,
        "code": "3.6",
        "name": "Business Travel",
        "description": "Flights, hotels, rental cars",
        "aggregates": ["3.6"],
    },
    {
        "scope": 3,
        "code": "3.7",
        "name": "Employee Commuting",
        "description": "Employees travelling to work",
        "aggregates": ["3.7"],
    },
    {
        "scope": 3,
        "code": "3.8",
        "name": "Upstream Leased Assets",
        "description": "Buildings, vehicles, equipment the company leases",
        "aggregates": ["3.8"],
    },
    # Scope 3 — Value chain (downstream)
    {
        "scope": 3,
        "code": "3.9",
        "name": "Downstream Transportation",
        "description": "Delivery of sold products to customers",
        "aggregates": ["3.9"],
    },
    {
        "scope": 3,
        "code": "3.10",
        "name": "Processing of Sold Products",
        "description": "Further processing by third parties",
        "aggregates": ["3.10"],
    },
    {
        "scope": 3,
        "code": "3.11",
        "name": "Use of Sold Products",
        "description": "Emissions when customers use the products",
        "aggregates": ["3.11"],
    },
    {
        "scope": 3,
        "code": "3.12",
        "name": "End-of-Life Treatment",
        "description": "Disposal of sold products",
        "aggregates": ["3.12"],
    },
    {
        "scope": 3,
        "code": "3.13",
        "name": "Downstream Leased Assets",
        "description": "Assets the company leases to others",
        "aggregates": ["3.13"],
    },
    {
        "scope": 3,
        "code": "3.14",
        "name": "Franchises",
        "description": "Franchise operations",
        "aggregates": ["3.14"],
    },
]

# code → canonical hub category dict
CATEGORY_BY_CODE: dict[str, dict] = {c["code"]: c for c in GHG_CATEGORIES}

# any ledger/staging category_code → the hub row code it rolls up into
HUB_CODE_FOR: dict[str, str] = {
    agg: c["code"] for c in GHG_CATEGORIES for agg in c["aggregates"]
}
