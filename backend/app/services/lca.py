"""
LCA-lite — the EN 15804 indicator × module results matrix on the PCF BOM.

Runs alongside the PCF compute: every BOM line that carries an activity_key
resolves an EF 3.1 impact vector from the impact_factors table (same
explicit-key, region-precedence culture as the emission factor lane), and
the characterized amounts are summed per indicator per EN 15804 module.

The climate row does NOT come from the impact table: it is the PCF
engine's per-line GWP (DEFRA/AR5, supplier PCFs included), so the platform
shows one climate number per product everywhere. The other 15 EF 3.1
indicators characterize from the curated library; lines without a dataset
are honest per-indicator gaps, never silent omissions.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.impact_factors import EF31_INDICATORS
from app.models.emission import ImpactFactor
from app.models.product import ProductInput, ProductInputType

METHOD_VERSION = "EF 3.1"

SCREENING_NOTE = (
    "Screening-grade LCA (EF 3.1 characterization, curated Climatrix library). "
    "Climate row = the PCF engine's GWP (DEFRA/AR5 + supplier primary data); "
    "remaining indicators are representative secondary values — confirm against "
    "a licensed LCI dataset before publishing a verified EPD."
)

# Full EN 15804 module vocabulary (A1-A3 = cradle-to-gate; D = benefits
# beyond the system boundary). Order is the standard's results-table order.
EN15804_MODULES = [
    "A1", "A2", "A3", "A4", "A5",
    "B1", "B2", "B3", "B4", "B5", "B6", "B7",
    "C1", "C2", "C3", "C4",
    "D",
]  # fmt: skip

CRADLE_TO_GATE_MODULES = {"A1", "A2", "A3"}

# Unit aliases + conversions into the impact table's activity units.
_UNIT_ALIASES = {
    "kg": "kg",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "t": "tonne",
    "tonne": "tonne",
    "tonnes": "tonne",
    "ton": "tonne",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kwh": "kWh",
    "mwh": "MWh",
    "l": "liters",
    "liter": "liters",
    "liters": "liters",
    "litre": "liters",
    "litres": "liters",
    "tkm": "tkm",
    "t-km": "tkm",
    "ton-km": "tkm",
    "tonne-km": "tkm",
    "ton_km": "tkm",
    "tonne_km": "tkm",
    "tonne-kilometer": "tkm",
}

# (from, to) -> multiplier, both sides in canonical alias form.
_CONVERSIONS = {
    ("kg", "kg"): Decimal("1"),
    ("tonne", "kg"): Decimal("1000"),
    ("g", "kg"): Decimal("0.001"),
    ("kWh", "kWh"): Decimal("1"),
    ("MWh", "kWh"): Decimal("1000"),
    ("liters", "liters"): Decimal("1"),
    ("tkm", "tkm"): Decimal("1"),
}


def convert_quantity(
    quantity: Decimal, from_unit: str, to_unit: str
) -> Optional[Decimal]:
    """Convert a BOM quantity into the impact dataset's activity unit.
    Returns None when the units are incompatible/unknown."""
    src = _UNIT_ALIASES.get(from_unit.strip().lower())
    dst = _UNIT_ALIASES.get(to_unit.strip().lower())
    if src is None or dst is None:
        return None
    if src == dst:
        return quantity
    multiplier = _CONVERSIONS.get((src, dst))
    return quantity * multiplier if multiplier is not None else None


def _sort_modules(modules) -> list[str]:
    order = {m: i for i, m in enumerate(EN15804_MODULES)}
    return sorted(modules, key=lambda m: order.get(m, len(order)))


async def compute_lca_matrix(
    session: AsyncSession,
    inputs: list[ProductInput],
    line_entries: list[dict],
    default_region: str,
) -> dict:
    """Build the indicator × module matrix from the PCF's computed lines.

    line_entries are the per-line dicts compute_footprint produced (they
    carry co2e_kg + en15804_module + status). Ready to persist as
    ProductFootprint.lca_results.
    """
    inputs_by_id = {str(i.id): i for i in inputs}
    dataset_keys = {i.activity_key for i in inputs if i.activity_key}

    vectors: dict[tuple[str, str], dict[str, ImpactFactor]] = {}
    if dataset_keys:
        rows = (
            (
                await session.execute(
                    select(ImpactFactor).where(
                        ImpactFactor.dataset_key.in_(dataset_keys),
                        ImpactFactor.is_active == True,  # noqa: E712
                        ImpactFactor.method_version == METHOD_VERSION,
                    )
                )
            )
            .scalars()
            .all()
        )
        for row in rows:
            vectors.setdefault((row.dataset_key, row.region), {})[
                row.indicator_code
            ] = row

    non_climate = [i for i in EF31_INDICATORS if i["code"] != "climate_change"]
    matrix: dict[str, dict[str, Decimal]] = {i["code"]: {} for i in EF31_INDICATORS}
    covered: dict[str, int] = {i["code"]: 0 for i in EF31_INDICATORS}
    gap_lines: dict[str, list[str]] = {i["code"]: [] for i in EF31_INDICATORS}
    line_coverage: list[dict] = []
    modules_present: set[str] = set()
    warnings: list[str] = []

    for entry in line_entries:
        line = inputs_by_id.get(entry["input_id"])
        module = (entry.get("en15804_module") or "A1").upper()
        modules_present.add(module)
        name = entry["name"]
        cov = {
            "input_id": entry["input_id"],
            "name": name,
            "en15804_module": module,
            "dataset": None,
            "dataset_region": None,
            "indicators_covered": 0,
            "note": None,
        }

        # Climate row: the PCF engine's GWP for this line (one number
        # platform-wide). A PCF gap is a climate gap too.
        if entry.get("status") == "ok":
            matrix["climate_change"][module] = matrix["climate_change"].get(
                module, Decimal("0")
            ) + Decimal(str(entry["co2e_kg"]))
            covered["climate_change"] += 1
            cov["indicators_covered"] += 1
        else:
            gap_lines["climate_change"].append(name)

        if line is None or not line.activity_key:
            if (
                line is not None
                and line.input_type == ProductInputType.SUPPLIER_PCF.value
            ):
                cov["note"] = (
                    "Supplier PCF covers the climate indicator only — ask the "
                    "supplier for an EPD/LCA dataset to fill the other 15"
                )
            else:
                cov["note"] = "No factor key — no EF 3.1 dataset to resolve"
            for ind in non_climate:
                gap_lines[ind["code"]].append(name)
            line_coverage.append(cov)
            continue

        region = line.region or default_region
        vector = vectors.get((line.activity_key, region)) or vectors.get(
            (line.activity_key, "Global")
        )
        if not vector:
            cov["note"] = (
                f"No EF 3.1 dataset for '{line.activity_key}' in the curated "
                "library yet — climate only"
            )
            for ind in non_climate:
                gap_lines[ind["code"]].append(name)
            line_coverage.append(cov)
            continue

        sample = next(iter(vector.values()))
        quantity = convert_quantity(
            Decimal(str(line.quantity_per_unit)), line.unit, sample.activity_unit
        )
        if quantity is None:
            cov["note"] = (
                f"Unit mismatch: BOM line is in {line.unit}, EF 3.1 dataset is "
                f"per {sample.activity_unit} — climate only"
            )
            for ind in non_climate:
                gap_lines[ind["code"]].append(name)
            line_coverage.append(cov)
            continue

        cov["dataset"] = sample.display_name
        cov["dataset_region"] = sample.region
        for ind in non_climate:
            code = ind["code"]
            factor = vector.get(code)
            if factor is None:
                gap_lines[code].append(name)
                continue
            matrix[code][module] = matrix[code].get(
                module, Decimal("0")
            ) + quantity * Decimal(str(factor.value))
            covered[code] += 1
            cov["indicators_covered"] += 1
        line_coverage.append(cov)

    total_lines = len(line_entries)
    uncovered = [c for c in line_coverage if c["dataset"] is None]
    if uncovered and total_lines:
        warnings.append(
            f"{len(uncovered)} of {total_lines} BOM lines have no EF 3.1 "
            "impact dataset — non-climate indicators are partial for: "
            + ", ".join(c["name"] for c in uncovered[:5])
            + ("…" if len(uncovered) > 5 else "")
        )

    modules = _sort_modules(modules_present)
    rows = []
    for ind in EF31_INDICATORS:
        code = ind["code"]
        by_module = {m: float(v) for m, v in matrix[code].items()}
        rows.append(
            {
                "code": code,
                "name": ind["name"],
                "unit": ind["unit"],
                "total": float(sum(matrix[code].values(), Decimal("0"))),
                "by_module": by_module,
                "covered_lines": covered[code],
                "total_lines": total_lines,
                "gap_lines": gap_lines[code],
            }
        )

    return {
        "method": METHOD_VERSION,
        "note": SCREENING_NOTE,
        "modules": modules,
        "rows": rows,
        "line_coverage": line_coverage,
        "warnings": warnings,
    }
