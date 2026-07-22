"""
PCF (Product Carbon Footprint) models — ISO 14067 / PACT Methodology v3.

Product + BOM (ProductInput) describe a product per declared unit;
SupplierPCF holds supplier-provided cradle-to-gate footprints (PACT exchange
or manual entry); ProductFootprint is the computed, snapshotted result.

Design mirrors the corporate lane: org-scoped rows, varchar statuses (no
native PG enums), JSON provenance payloads, immutable-once-final snapshots
(the verifier-portal pattern, one level down: product instead of org).
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, SQLModel
from sqlalchemy import Column as SAColumn
from sqlalchemy import String as SAString


class ProductInputType(str, Enum):
    """What a BOM line represents (drives calculator + stage breakdown)."""

    PURCHASED_MATERIAL = "purchased_material"  # raw/intermediate goods (A1)
    ENERGY = "energy"  # electricity/fuel of own processes (A3)
    TRANSPORT = "transport"  # inbound logistics (A2)
    PROCESS = "process"  # direct process/combustion emissions (A3)
    SUPPLIER_PCF = "supplier_pcf"  # supplier-provided cradle-to-gate PCF (A1)


class FootprintStatus(str, Enum):
    DRAFT = "draft"
    FINAL = "final"


class EPDStatus(str, Enum):
    """ISO 14025 declaration lifecycle. Transitions move one step at a time
    (enforced in services/epd.py); published EPDs expire after 5 years."""

    DRAFT = "draft"
    INTERNAL_REVIEW = "internal_review"
    VERIFICATION = "verification"
    REGISTERED = "registered"
    PUBLISHED = "published"
    EXPIRED = "expired"


class Product(SQLModel, table=True):
    """An org's product/SKU whose footprint is modeled per declared unit."""

    __tablename__ = "products"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    name: str = Field(max_length=255)
    sku: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    # PACT declared unit: kilogram | tonne | piece | kilowatt_hour | liter |
    # cubic_meter | square_meter | megajoule | ton_kilometer
    declared_unit: str = Field(default="kilogram", max_length=30)
    declared_unit_amount: Decimal = Field(default=Decimal("1"))
    cn_code: Optional[str] = Field(default=None, max_length=10, index=True)  # CBAM link
    category: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    is_demo: bool = Field(default=False)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


class ProductInput(SQLModel, table=True):
    """One BOM line: a quantified input per declared unit of the product."""

    __tablename__ = "product_inputs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    product_id: UUID = Field(foreign_key="products.id", index=True)
    input_type: str = Field(
        default=ProductInputType.PURCHASED_MATERIAL.value,
        sa_column=SAColumn(
            "input_type", SAString(30), default="purchased_material", nullable=False
        ),
    )
    name: str = Field(max_length=255)
    quantity_per_unit: Decimal
    unit: str = Field(max_length=50)
    # Factor grounding: either a factor-library key OR a supplier PCF reference.
    activity_key: Optional[str] = Field(default=None, max_length=100, index=True)
    supplier_pcf_id: Optional[UUID] = Field(
        default=None, foreign_key="supplier_pcfs.id"
    )
    # Optional overrides for factor resolution; defaults derived from input_type.
    category_code: Optional[str] = Field(default=None, max_length=10)
    scope: Optional[int] = Field(default=None, ge=1, le=3)
    region: Optional[str] = Field(default=None, max_length=50)
    # EN 15804 lifecycle module tag — makes the BOM LCA-ready (A1 materials,
    # A2 inbound transport, A3 own production).
    en15804_module: str = Field(default="A1", max_length=5)
    notes: Optional[str] = Field(default=None, max_length=500)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


class SupplierPCF(SQLModel, table=True):
    """A supplier-provided product footprint (PACT exchange file or manual).

    Primary data on the PACT ladder — BOM lines referencing one lift the
    product's primary-data share.
    """

    __tablename__ = "supplier_pcfs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    supplier_name: str = Field(max_length=255)
    product_name: str = Field(max_length=255)  # supplier's product
    pcf_value: Decimal  # kg CO2e per unit
    unit: str = Field(max_length=50)  # unit the value is per (kg, tonne, kWh…)
    boundary: str = Field(default="cradle_to_gate", max_length=30)
    primary_data_share: Optional[float] = Field(default=None, ge=0, le=100)
    valid_until: Optional[date] = Field(default=None)
    # PACT traceability: the supplier file's ProductFootprint id + raw payload.
    pact_pf_id: Optional[str] = Field(default=None, max_length=64)
    source: str = Field(default="manual", max_length=20)  # manual | pact_json
    raw_payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # Seeded by "Load sample data"; removed wholesale by DELETE /sample-data
    is_demo: bool = Field(default=False)
    status: str = Field(
        default="active",
        sa_column=SAColumn("status", SAString(20), default="active", nullable=False),
    )
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProductFootprint(SQLModel, table=True):
    """Computed PCF snapshot for a product in a reporting period.

    line_items carries the full per-line derivation story (factor, region,
    formula, warnings) — same provenance culture as Smart Import grounding.
    Immutable once status=final.
    """

    __tablename__ = "product_footprints"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    product_id: UUID = Field(foreign_key="products.id", index=True)
    reporting_period_id: UUID = Field(foreign_key="reporting_periods.id", index=True)
    declared_unit: str = Field(max_length=30)
    declared_unit_amount: Decimal = Field(default=Decimal("1"))
    boundary: str = Field(default="cradle_to_gate", max_length=30)
    total_kgco2e_per_unit: Decimal
    fossil_kgco2e_per_unit: Optional[Decimal] = Field(default=None)
    biogenic_kgco2e_per_unit: Optional[Decimal] = Field(default=None)
    primary_data_share: Optional[float] = Field(default=None, ge=0, le=100)
    stage_breakdown: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    line_items: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
    warnings: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    methodology: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # LCA-lite: EF 3.1 indicator × EN 15804 module matrix, frozen with the
    # snapshot (the results table a future EPD version pins to).
    lca_results: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(
        default="draft",
        sa_column=SAColumn("status", SAString(20), default="draft", nullable=False),
    )
    finalized_at: Optional[datetime] = Field(default=None)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EPDProject(SQLModel, table=True):
    """An Environmental Product Declaration in preparation (ISO 14025).

    Climatrix prepares the EPD — models the product, computes the EN 15804
    results matrix, generates the declaration documents, runs the
    verification workflow. Issuing/publishing stays with the program
    operator + third-party verifier (same insight as the verifier portal:
    we don't replace the auditor, we make the audit frictionless).

    `results` is a frozen copy of the pinned footprint's PCF totals +
    lca_results, captured when the project leaves draft — from that moment
    the declaration content is version-stable regardless of later
    recomputes on the product.
    """

    __tablename__ = "epd_projects"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    product_id: UUID = Field(foreign_key="products.id", index=True)
    # The finalized footprint snapshot this EPD version pins to.
    footprint_id: Optional[UUID] = Field(
        default=None, foreign_key="product_footprints.id"
    )
    name: str = Field(max_length=255)
    # Product Category Rules — EN 15804+A2 first; PCR registry table later.
    pcr: str = Field(default="EN 15804+A2", max_length=100)
    program_operator: Optional[str] = Field(default=None, max_length=255)
    declared_unit: str = Field(default="kilogram", max_length=30)
    declared_unit_amount: Decimal = Field(default=Decimal("1"))
    # Optional functional unit (declared unit suffices for cradle-to-gate).
    functional_unit: Optional[str] = Field(default=None, max_length=255)
    # Reference service life — required when B modules are declared.
    rsl_years: Optional[int] = Field(default=None, ge=1, le=200)
    # EN 15804 modules declared in scope (JSON list, e.g. A1-A3 + C + D).
    scope_modules: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(
        default="draft",
        sa_column=SAColumn("status", SAString(30), default="draft", nullable=False),
    )
    version: int = Field(default=1)
    # Frozen results (PCF totals + LCA matrix) — set when leaving draft.
    results: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    results_frozen_at: Optional[datetime] = Field(default=None)
    registration_number: Optional[str] = Field(default=None, max_length=100)
    registered_at: Optional[datetime] = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)
    # ISO 14025 / EN 15804: 5-year validity from publication.
    valid_until: Optional[date] = Field(default=None)
    verifier_statement: Optional[str] = Field(default=None, max_length=2000)
    notes: Optional[str] = Field(default=None, max_length=2000)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
