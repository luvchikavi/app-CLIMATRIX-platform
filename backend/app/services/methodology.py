"""Single source of truth for GHG methodology statements and policy.

Every consumer of methodology text or policy — the ISO 14064 / CDP / ESRS
report builders, the ingestion parser, and the frontend (via
GET /reference/methodology) — reads from here. Endpoints and components
must never hardcode a GWP statement, a consolidation-approach label, or a
data-quality tier boundary of their own: when the methodology changes, it
changes in this one file.
"""

from typing import Optional

# ---------------------------------------------------------------------------
# GWP basis
# ---------------------------------------------------------------------------

GWP_SOURCE = "IPCC AR6 (2021) - 100-year GWP values"
GWP_STATEMENT = "IPCC AR6 100-year GWP values (CO2=1, CH4=27.9, N2O=273)"

# ---------------------------------------------------------------------------
# Accounting standard & calculation approach
# ---------------------------------------------------------------------------

GHG_ACCOUNTING_STANDARD = "GHG Protocol Corporate Standard"
CALCULATION_APPROACH = "Activity-based calculations using GHG Protocol methodology"

# ---------------------------------------------------------------------------
# Organizational boundary (GHG Protocol Corporate Standard ch. 3)
# ---------------------------------------------------------------------------

DEFAULT_CONSOLIDATION_APPROACH = "operational_control"

CONSOLIDATION_APPROACH_LABELS = {
    "operational_control": "Operational control",
    "financial_control": "Financial control",
    "equity_share": "Equity share",
}


def consolidation_label(approach: Optional[str]) -> str:
    """Human-readable label for an org's consolidation approach.

    Falls back to the operational-control default when the org has not set
    one (the field default on Organization).
    """
    key = approach or DEFAULT_CONSOLIDATION_APPROACH
    return CONSOLIDATION_APPROACH_LABELS.get(
        key, CONSOLIDATION_APPROACH_LABELS[DEFAULT_CONSOLIDATION_APPROACH]
    )


# ---------------------------------------------------------------------------
# Data-quality ladder (PCAF 1-5 → measure/estimate tier)
# ---------------------------------------------------------------------------

DATA_QUALITY_TIERS = [
    {
        "tier": "measured",
        "scores": [1, 2],
        "description": "Primary or verified data (metered, invoiced with quantity)",
    },
    {
        "tier": "calculated",
        "scores": [3],
        "description": "Activity data with average emission factors",
    },
    {
        "tier": "estimated",
        "scores": [4, 5],
        "description": "Spend-based or proxy estimates (EEIO)",
    },
]


def tier_of_score(score: Optional[int]) -> str:
    """Canonical PCAF-score → ladder-tier mapping (hub, reports, parser)."""
    if score is None:
        return "estimated"
    if score <= 2:
        return "measured"
    if score == 3:
        return "calculated"
    return "estimated"


# ---------------------------------------------------------------------------
# Method hierarchy (Scope 3 Calculation Guidance)
# ---------------------------------------------------------------------------

METHOD_HIERARCHY = [
    {
        "method": "supplier",
        "label": "Supplier-specific",
        "description": "Emission factor provided by the supplier (EPD, primary data)",
    },
    {
        "method": "ecoinvent",
        "label": "Process database",
        "description": "Process-level LCA database factor",
    },
    {
        "method": "defra_physical",
        "label": "Average-data (physical)",
        "description": "Physical quantity × published average factor",
    },
    {
        "method": "eeio_spend",
        "label": "Spend-based (EEIO)",
        "description": "Monetary spend × environmentally-extended input-output factor",
    },
]

# ---------------------------------------------------------------------------
# Biogenic CO2 (reported separately, outside the scopes)
# ---------------------------------------------------------------------------

BIOGENIC_POLICY = (
    "Biogenic CO2 from biofuel and biomass combustion is excluded from "
    "Scope 1 and reported separately outside the scopes, per the GHG "
    "Protocol Corporate Standard. CH4 and N2O from the same combustion "
    "remain in Scope 1."
)


# ---------------------------------------------------------------------------
# Base-year recalculation policy (GHG Protocol Corporate Standard ch. 5)
# ---------------------------------------------------------------------------

DEFAULT_RECALCULATION_THRESHOLD_PCT = 5.0


def recalculation_policy_statement(
    base_year: Optional[int], threshold_pct: Optional[float]
) -> str:
    """The org's base-year recalculation policy as report-ready prose."""
    threshold = (
        threshold_pct
        if threshold_pct is not None
        else DEFAULT_RECALCULATION_THRESHOLD_PCT
    )
    policy = (
        "Base-year emissions are recalculated when structural changes "
        "(acquisitions, divestments, mergers), methodology changes, or the "
        "discovery of significant errors alter base-year emissions by more "
        f"than {threshold:g}% (significance threshold), per the GHG Protocol "
        "Corporate Standard."
    )
    if base_year:
        return f"Base year: {base_year}. {policy}"
    return (
        "No base year has been set; the first complete reporting year will "
        f"be adopted as the base year. {policy}"
    )


def build_assumptions(consolidation_approach: Optional[str]) -> list[str]:
    """Standard methodology assumptions, reflecting the org's real settings."""
    return [
        f"{consolidation_label(consolidation_approach)} approach for "
        "organizational boundaries",
        "Location-based method for Scope 2 unless market-based data available",
        "Average emission factors used where supplier-specific data unavailable",
    ]


def methodology_reference() -> dict:
    """The full methodology description served to the frontend.

    UI surfaces (report pages, hub explanations, import review) render from
    this payload instead of hardcoding methodology strings.
    """
    return {
        "ghg_accounting_standard": GHG_ACCOUNTING_STANDARD,
        "calculation_approach": CALCULATION_APPROACH,
        "gwp_source": GWP_SOURCE,
        "gwp_statement": GWP_STATEMENT,
        "consolidation_approaches": [
            {"value": value, "label": label}
            for value, label in CONSOLIDATION_APPROACH_LABELS.items()
        ],
        "data_quality_tiers": DATA_QUALITY_TIERS,
        "method_hierarchy": METHOD_HIERARCHY,
        "biogenic_policy": BIOGENIC_POLICY,
    }
