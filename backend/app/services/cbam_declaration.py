"""
CBAM annual declaration draft builder (definitive regime, 2026+).

Builds a complete declaration draft from the imports register:

- Per-line embedded emissions: lines with actual installation data keep the
  values recorded on the import; default-value lines are re-resolved against
  the Commission default values stored in the DB (per CN code x origin
  country) and carry the Omnibus year markup (10% 2026, 20% 2027, 30% from
  2028 — Reg. (EU) 2025/2083).
- Carbon-price-paid deductions summed from the import lines (the
  `carbon_price_paid_eur` field, EUR/tCO2e), capped at the CBAM cost.
- Certificates to surrender: 1 certificate = 1 tCO2e, rounded up to a whole
  certificate on the annual total.
- Certificate cost at the EU ETS price supplied by the caller (latest
  stored price, or the explicit fallback).
- Data-quality summary: how many lines rest on default values vs actual
  data, and how many defaults lack a Commission DB row.
- An explicit `assumptions` list, consistent with the platform's
  verification-ready philosophy.

Pure module: callers load the imports, default-value rows and ETS price and
pass them in; nothing here touches the database.
"""

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Optional

from app.models.cbam import CBAMImport
from app.services.cbam_calculator import CBAMCalculator
from app.services.cbam_screening import resolve_default_intensity

_calculator = CBAMCalculator()

_REGISTRY_ON_HOLD_ASSUMPTION = (
    "Submission to the CBAM Registry is on hold until the export is "
    "validated against the real CBAM Registry declaration schema; this "
    "draft is a preparation pack, not a filing."
)


def default_markup_for_year(year: int) -> Decimal:
    """Omnibus default-value markup: 10% (2026), 20% (2027), 30% (2028+)."""
    if year <= 2026:
        return Decimal("0.10")
    if year == 2027:
        return Decimal("0.20")
    return Decimal("0.30")


def _q3(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _enum_value(value) -> Optional[str]:
    return getattr(value, "value", value)


def _new_sector_bucket() -> dict:
    return {
        "import_count": 0,
        "mass_tonnes": Decimal("0"),
        "gross_emissions_tco2e": Decimal("0"),
        "deductions_tco2e": Decimal("0"),
        "net_emissions_tco2e": Decimal("0"),
        "certificates_required": Decimal("0"),
        "estimated_cost_eur": Decimal("0"),
        "default_lines": 0,
        "actual_lines": 0,
    }


def _new_cn_bucket() -> dict:
    return {
        "import_count": 0,
        "mass_tonnes": Decimal("0"),
        "gross_emissions_tco2e": Decimal("0"),
        "net_emissions_tco2e": Decimal("0"),
        "estimated_cost_eur": Decimal("0"),
        "countries": set(),
    }


def build_annual_declaration_draft(
    imports: list[CBAMImport],
    year: int,
    ets_price_eur: Decimal,
    default_values: Optional[list[dict]] = None,
    extra_assumptions: Optional[list[str]] = None,
) -> dict:
    """
    Build the annual declaration draft package for one org-year.

    `default_values` rows are plain dicts (see
    `cbam_screening.resolve_default_intensity`): {"cn_code", "country_code",
    "total_see", "source"}.

    Returns totals, per-sector and per-CN breakdowns, per-line detail with
    intensity provenance, a data-quality summary and the assumptions list.
    """
    markup = default_markup_for_year(year)
    assumptions: list[str] = list(extra_assumptions or [])

    lines: list[dict] = []
    by_sector: dict[str, dict] = {}
    by_cn: dict[str, dict] = {}

    total_mass = Decimal("0")
    gross_total = Decimal("0")
    deductions_tco2e_total = Decimal("0")
    deductions_eur_total = Decimal("0")
    net_total = Decimal("0")

    actual_lines = 0
    default_lines = 0
    lines_without_db_default = 0

    for imp in imports:
        mass = imp.net_mass_tonnes or Decimal("0")
        method = _enum_value(imp.calculation_method) or "default"
        sector = _enum_value(imp.sector) or "unknown"
        is_actual = method == "actual"

        if is_actual:
            actual_lines += 1
            emissions = imp.total_embedded_emissions_tco2e or Decimal("0")
            see = (emissions / mass) if mass > 0 else Decimal("0")
            line_markup = Decimal("0")
            source_detail = "actual installation data recorded on the import"
        else:
            default_lines += 1
            base_see, source_ref = resolve_default_intensity(
                imp.cn_code, imp.origin_country, None, default_values
            )
            if base_see is None:
                lines_without_db_default += 1
                base_see = imp.specific_embedded_emissions or (
                    (imp.total_embedded_emissions_tco2e or Decimal("0")) / mass
                    if mass > 0
                    else Decimal("0")
                )
                source_ref = (
                    "import-time default value (no Commission default value "
                    "in the reference database for this CN code)"
                )
            line_markup = markup
            see = base_see * (Decimal("1") + markup)
            emissions = see * mass
            source_detail = source_ref

        emissions = _q3(emissions)

        deduction = _calculator.calculate_carbon_price_deduction(
            total_emissions_tco2e=emissions,
            foreign_carbon_price_eur=imp.carbon_price_paid_eur,
            eu_ets_price_eur=ets_price_eur,
        )
        deduction_tco2e = deduction["deduction_tco2e"]
        deduction_eur = deduction["deduction_eur"]
        net = deduction["net_emissions_tco2e"]
        cost = _q2(net * ets_price_eur)

        lines.append(
            {
                "import_id": str(imp.id),
                "import_date": imp.import_date,
                "cn_code": imp.cn_code,
                "sector": sector,
                "product_description": imp.product_description,
                "origin_country": imp.origin_country,
                "mass_tonnes": _q3(mass),
                "intensity_source": "actual" if is_actual else "default",
                "intensity_source_detail": source_detail,
                "see_tco2e_per_tonne": _q3(see),
                "markup_pct": _q2(line_markup * 100),
                "emissions_tco2e": emissions,
                "deduction_tco2e": deduction_tco2e,
                "deduction_eur": deduction_eur,
                "net_emissions_tco2e": _q3(net),
                "estimated_cost_eur": cost,
            }
        )

        sector_bucket = by_sector.setdefault(sector, _new_sector_bucket())
        sector_bucket["import_count"] += 1
        sector_bucket["mass_tonnes"] += mass
        sector_bucket["gross_emissions_tco2e"] += emissions
        sector_bucket["deductions_tco2e"] += deduction_tco2e
        sector_bucket["net_emissions_tco2e"] += net
        sector_bucket["certificates_required"] += net
        sector_bucket["estimated_cost_eur"] += cost
        sector_bucket["default_lines" if not is_actual else "actual_lines"] += 1

        cn_bucket = by_cn.setdefault(imp.cn_code, _new_cn_bucket())
        cn_bucket["import_count"] += 1
        cn_bucket["mass_tonnes"] += mass
        cn_bucket["gross_emissions_tco2e"] += emissions
        cn_bucket["net_emissions_tco2e"] += net
        cn_bucket["estimated_cost_eur"] += cost
        cn_bucket["countries"].add(imp.origin_country or "")

        total_mass += mass
        gross_total += emissions
        deductions_tco2e_total += deduction_tco2e
        deductions_eur_total += deduction_eur
        net_total += net

    # 1 certificate = 1 tCO2e, rounded UP to whole certificates on the total.
    certificates_required = int(net_total.to_integral_value(rounding=ROUND_CEILING))

    for bucket in by_sector.values():
        for key in (
            "mass_tonnes",
            "gross_emissions_tco2e",
            "deductions_tco2e",
            "net_emissions_tco2e",
            "certificates_required",
        ):
            bucket[key] = _q3(bucket[key])
        bucket["estimated_cost_eur"] = _q2(bucket["estimated_cost_eur"])

    for bucket in by_cn.values():
        for key in ("mass_tonnes", "gross_emissions_tco2e", "net_emissions_tco2e"):
            bucket[key] = _q3(bucket[key])
        bucket["estimated_cost_eur"] = _q2(bucket["estimated_cost_eur"])
        bucket["countries"] = sorted(c for c in bucket["countries"] if c)

    total_lines = len(lines)
    default_share_pct = (
        round(default_lines * 100 / total_lines, 1) if total_lines else 0.0
    )

    assumptions.append(
        f"Default-value lines carry the {year} markup of "
        f"{_q2(markup * 100)}% on the default emission intensity "
        "(Omnibus, Reg. (EU) 2025/2083: 10% in 2026, 20% in 2027, 30% from "
        "2028); lines with actual installation data carry no markup."
    )
    if lines_without_db_default:
        assumptions.append(
            f"{lines_without_db_default} default-value line(s) have no "
            "Commission default value in the reference database for their "
            "CN code — the emission intensity recorded at import time was "
            "used instead (plus the year markup)."
        )
    assumptions.append(
        "Carbon prices effectively paid in the country of origin are "
        "deducted per import line and capped at the CBAM cost of the line; "
        "the deduction is an estimate — the implementing act on "
        "third-country carbon price deductions is not yet final."
    )
    assumptions.append(
        "1 CBAM certificate = 1 tCO2e; the certificates to surrender are "
        "the annual net embedded emissions rounded up to whole certificates. "
        "The estimated cost applies the ETS price to the fractional net "
        "emissions."
    )
    assumptions.append(_REGISTRY_ON_HOLD_ASSUMPTION)

    return {
        "year": year,
        "ets_price_eur": _q2(ets_price_eur),
        "markup_pct": _q2(markup * 100),
        "totals": {
            "import_count": total_lines,
            "mass_tonnes": _q3(total_mass),
            "gross_emissions_tco2e": _q3(gross_total),
            "deductions_tco2e": _q3(deductions_tco2e_total),
            "deductions_eur": _q2(deductions_eur_total),
            "net_emissions_tco2e": _q3(net_total),
            "certificates_required": certificates_required,
            "estimated_cost_eur": _q2(net_total * ets_price_eur),
        },
        "by_sector": by_sector,
        "by_cn_code": by_cn,
        "lines": lines,
        "data_quality": {
            "total_lines": total_lines,
            "actual_lines": actual_lines,
            "default_lines": default_lines,
            "default_share_pct": default_share_pct,
            "lines_without_db_default": lines_without_db_default,
        },
        "assumptions": assumptions,
    }
