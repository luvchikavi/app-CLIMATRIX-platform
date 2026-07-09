"""
CBAM screening service — stateless "am I in scope?" checker.

Implements the Omnibus (Reg. (EU) 2025/2083) de minimis rule for the
definitive regime: a 50,000 kg cumulative annual threshold across iron &
steel, aluminium, fertilisers and cement ONLY. Hydrogen and electricity are
always in scope — no threshold applies to them.

Emission intensities here are conservative representative defaults per
sector; the official Commission 13-Feb-2026 default values (per CN code and
origin country) are loaded in Phase 1b. Every simplification is surfaced in
the `assumptions` list of the result.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Union

# Omnibus de minimis: 50 t net mass per calendar year, cumulative.
DE_MINIMIS_THRESHOLD_KG = Decimal("50000")

# Sectors the cumulative threshold applies to. Hydrogen and electricity are
# deliberately excluded: they are in scope from the first kg / kWh.
DE_MINIMIS_SECTORS = frozenset({"cement", "iron_steel", "aluminium", "fertiliser"})
ALWAYS_IN_SCOPE_SECTORS = frozenset({"hydrogen", "electricity"})

# Markup on default values in 2026 (20% in 2027, 30% from 2028).
DEFAULT_VALUE_MARKUP_2026 = Decimal("0.10")

# Conservative representative default emission intensities.
# tCO2e per tonne of product; electricity is tCO2e per MWh.
# Source: representative default, Commission 13-Feb-2026 values to be loaded
# in Phase 1b.
SECTOR_DEFAULT_INTENSITY = {
    "cement": Decimal("0.95"),
    "iron_steel": Decimal("2.5"),
    "aluminium": Decimal("8.0"),
    "fertiliser": Decimal("2.5"),
    "hydrogen": Decimal("12.0"),
    "electricity": Decimal("0.75"),
}

SECTOR_LABELS = {
    "cement": "Cement",
    "iron_steel": "Iron & steel",
    "aluminium": "Aluminium",
    "fertiliser": "Fertilisers",
    "hydrogen": "Hydrogen",
    "electricity": "Electricity",
}

# Direct sector names (and common variants) accepted in place of a CN code.
_SECTOR_ALIASES = {
    "cement": "cement",
    "iron_steel": "iron_steel",
    "iron and steel": "iron_steel",
    "iron & steel": "iron_steel",
    "steel": "iron_steel",
    "iron": "iron_steel",
    "aluminium": "aluminium",
    "aluminum": "aluminium",
    "fertiliser": "fertiliser",
    "fertilisers": "fertiliser",
    "fertilizer": "fertiliser",
    "fertilizers": "fertiliser",
    "hydrogen": "hydrogen",
    "electricity": "electricity",
}

# CN-code prefix → sector (Annex I, Reg. 2023/956). Longest prefix wins.
# Extends the transitional-era table in app/data/cbam_data.py with a plain
# "2804" hydrogen prefix so screening accepts 4-digit codes.
_CN_PREFIX_SECTORS = [
    ("280410", "hydrogen"),
    ("283421", "fertiliser"),
    ("2523", "cement"),
    ("2716", "electricity"),
    ("2804", "hydrogen"),
    ("2808", "fertiliser"),
    ("2814", "fertiliser"),
    ("3102", "fertiliser"),
    ("3105", "fertiliser"),
    ("72", "iron_steel"),
    ("73", "iron_steel"),
    ("76", "aluminium"),
]


def resolve_sector(cn_code_or_sector: str) -> Optional[str]:
    """Map a CN code (any common formatting) or a sector name to a CBAM sector."""
    value = (cn_code_or_sector or "").strip().lower()
    if not value:
        return None

    normalized = value.replace("-", "_")
    if normalized in _SECTOR_ALIASES:
        return _SECTOR_ALIASES[normalized]

    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None

    for prefix, sector in _CN_PREFIX_SECTORS:
        if digits.startswith(prefix):
            return sector

    return None


def _to_decimal(value: Union[Decimal, float, int, str]) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def resolve_default_intensity(
    cn_code_or_sector: str,
    origin_country: Optional[str],
    sector: Optional[str],
    default_values: Optional[list[dict]] = None,
) -> tuple[Optional[Decimal], str]:
    """
    Resolve the default emission intensity (tCO2e/t; tCO2e/MWh for
    electricity) for one import line.

    Preference order:
    1. DB default value matching the longest CN-code prefix AND the origin
       country (Commission definitive defaults are per CN x country).
    2. DB default value matching the longest CN-code prefix with no country
       (country-independent fallback row).
    3. Hardcoded sector representative value (`SECTOR_DEFAULT_INTENSITY`).

    `default_values` rows are plain dicts so the function stays pure and
    testable: {"cn_code": str, "country_code": str | None,
    "total_see": Decimal-like, "source": str}.

    Returns (intensity, source_label); intensity is None when the line
    cannot be resolved at all.
    """
    digits = "".join(ch for ch in (cn_code_or_sector or "") if ch.isdigit())
    country = (origin_country or "").strip().upper()
    country = country if len(country) == 2 else ""

    best_with_country: Optional[tuple[int, dict]] = None
    best_any_country: Optional[tuple[int, dict]] = None

    if digits and default_values:
        for row in default_values:
            row_cn = "".join(ch for ch in str(row.get("cn_code") or "") if ch.isdigit())
            if not row_cn or not digits.startswith(row_cn):
                continue
            row_country = (row.get("country_code") or "").strip().upper()
            if row_country:
                if country and row_country == country:
                    if best_with_country is None or len(row_cn) > best_with_country[0]:
                        best_with_country = (len(row_cn), row)
            else:
                if best_any_country is None or len(row_cn) > best_any_country[0]:
                    best_any_country = (len(row_cn), row)

    match = best_with_country or best_any_country
    if match:
        row = match[1]
        return (
            _to_decimal(row["total_see"]),
            str(row.get("source") or "database default value"),
        )

    if sector:
        return SECTOR_DEFAULT_INTENSITY[sector], "representative_v0"

    return None, "unresolved"


def _round(value: Decimal, places: str) -> float:
    return float(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def screen_imports(
    items: list[dict],
    ets_price_eur: Union[Decimal, float],
    extra_assumptions: Optional[list[str]] = None,
    default_values: Optional[list[dict]] = None,
) -> dict:
    """
    Screen a basket of annual import lines against the CBAM definitive regime.

    Each item: {"cn_code_or_sector": str, "mass_kg": number,
    "origin_country": str | None}. For electricity lines the quantity is
    interpreted as kWh (electricity has no meaningful net mass).

    `default_values` (optional) is a list of DB default-value rows (see
    `resolve_default_intensity`); when provided, per-CN x origin-country
    values are preferred over the sector representative constants. The
    function stays pure — callers load the rows and pass them in.

    Returns the screening verdict with per-line estimates and an explicit
    list of every simplifying assumption made.
    """
    ets_price = _to_decimal(ets_price_eur)
    assumptions: list[str] = list(extra_assumptions or [])

    resolved = []
    in_threshold_mass_kg = Decimal("0")
    for item in items:
        raw = item.get("cn_code_or_sector") or ""
        mass_kg = _to_decimal(item.get("mass_kg") or 0)
        sector = resolve_sector(raw)
        resolved.append((item, sector, mass_kg))
        if sector in DE_MINIMIS_SECTORS:
            in_threshold_mass_kg += mass_kg

    over_threshold = in_threshold_mass_kg >= DE_MINIMIS_THRESHOLD_KG
    headroom_kg = max(Decimal("0"), DE_MINIMIS_THRESHOLD_KG - in_threshold_mass_kg)

    result_items = []
    total_emissions = Decimal("0")
    total_cost = Decimal("0")
    has_always_in_scope = False
    has_electricity = False
    has_unknown = False
    intensity_sources_used: set[str] = set()

    for item, sector, mass_kg in resolved:
        counts_toward_threshold = sector in DE_MINIMIS_SECTORS
        if sector in ALWAYS_IN_SCOPE_SECTORS:
            covered = True
            has_always_in_scope = True
        elif counts_toward_threshold:
            covered = over_threshold
        else:
            covered = False
            has_unknown = True
            assumptions.append(
                f"Line '{item.get('cn_code_or_sector')}' could not be mapped to a "
                "CBAM sector — treated as outside CBAM scope."
            )

        emissions = Decimal("0")
        cost = Decimal("0")
        intensity_source: Optional[str] = None
        if sector:
            if sector == "electricity":
                has_electricity = True
            intensity, intensity_source = resolve_default_intensity(
                item.get("cn_code_or_sector") or "",
                item.get("origin_country"),
                sector,
                default_values,
            )
            intensity_sources_used.add(intensity_source)
            # mass_kg / 1000 = tonnes (or, for electricity, kWh / 1000 = MWh).
            emissions = (
                (mass_kg / Decimal("1000"))
                * intensity
                * (Decimal("1") + DEFAULT_VALUE_MARKUP_2026)
            )
            if covered:
                cost = emissions * ets_price
                total_emissions += emissions
                total_cost += cost

        result_items.append(
            {
                "cn_code_or_sector": item.get("cn_code_or_sector"),
                "sector": sector,
                "sector_label": SECTOR_LABELS.get(sector) if sector else None,
                "origin_country": item.get("origin_country"),
                "mass_kg": float(mass_kg),
                "covered": covered,
                "counts_toward_threshold": counts_toward_threshold,
                "intensity_source": intensity_source,
                "estimated_emissions_tco2e": _round(emissions, "0.001"),
                "estimated_certificate_cost_eur": _round(cost, "0.01"),
            }
        )

    # Exempt = under the 50 t threshold AND no goods that are always in scope.
    exempt = not over_threshold and not has_always_in_scope

    non_representative = intensity_sources_used - {"representative_v0", "unresolved"}
    if non_representative:
        assumptions.append(
            "Embedded emissions use default values from the reference "
            f"database (sources: {', '.join(sorted(non_representative))}"
            + (
                "; representative sector fallbacks used for some lines"
                if "representative_v0" in intensity_sources_used
                else ""
            )
            + "), resolved per CN code and origin country where available."
        )
    else:
        assumptions.append(
            "Embedded emissions use conservative sector-level "
            "representative default intensities (source: representative_v0; "
            "load the Commission 13-Feb-2026 default values via "
            "`load-cbam-defaults` for per-CN x country precision)."
        )
    assumptions.extend(
        [
            (
                "The 2026 default-value markup of 10% is applied to every "
                "estimate (rises to 20% in 2027 and 30% from 2028)."
            ),
            (
                "The 50,000 kg de minimis is cumulative across iron & steel, "
                "aluminium, fertilisers and cement only; hydrogen and "
                "electricity are always in scope with no threshold."
            ),
            (
                f"Certificate cost = estimated embedded emissions x "
                f"€{_round(ets_price, '0.01')}/tCO2e; 2026 certificates will "
                "be priced on quarterly EU ETS auction averages."
            ),
            (
                "Carbon prices already paid in the country of origin are not "
                "deducted in this screening estimate."
            ),
        ]
    )
    if has_electricity:
        assumptions.append(
            "Electricity lines: quantity is interpreted as kWh and a default "
            "intensity of 0.75 tCO2e/MWh is applied."
        )
    if has_unknown:
        assumptions.append(
            "Unmapped lines are excluded from the threshold and cost totals — "
            "verify their CN codes against Annex I of Reg. (EU) 2023/956."
        )

    return {
        "threshold_kg": float(DE_MINIMIS_THRESHOLD_KG),
        "in_threshold_mass_kg": float(in_threshold_mass_kg),
        "headroom_kg": float(headroom_kg),
        "exempt": exempt,
        "ets_price_eur": _round(ets_price, "0.01"),
        "default_value_markup_pct": float(DEFAULT_VALUE_MARKUP_2026 * 100),
        "total_estimated_emissions_tco2e": _round(total_emissions, "0.001"),
        "total_estimated_certificate_cost_eur": _round(total_cost, "0.01"),
        "items": result_items,
        "assumptions": assumptions,
    }
