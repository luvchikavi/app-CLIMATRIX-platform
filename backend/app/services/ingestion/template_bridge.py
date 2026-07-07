"""Template bridge — the deterministic fast path inside Smart Import.

When an upload IS the CLIMATRIX template (our own export — known sheet names,
known columns), sending it through the generic LLM funnel is both wasteful and
lossy: the template's semantics (Calc_Type physical/spend switching, airport
pairs → flight distance, employees × days × distance commuting math) are exact,
so we parse it with the existing :class:`TemplateParser` and stage the result
directly. No LLM calls, near-instant, and the only clarifying questions left are
real grounding blockers (unit vs factor mismatches), not "which activity is TLV".

Foreign files never enter this path — detection requires multiple exact template
sheet names.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import openpyxl

from app.services.ingestion.mapper import MappedRow, _json_safe
from app.services.template_parser.parser import TemplateParser
from app.services.template_parser.sheet_config import SHEET_CONFIGS

# Require several exact sheet-name matches so a coincidental "3.5" tab in a
# client's own workbook doesn't trigger the template path.
_MIN_TEMPLATE_SHEETS = 2

_XLSX_EXTENSIONS = (".xlsx", ".xlsm")

# Freight factors are per tonne-km; the template records weight + Distance_km on
# each transport row, so the conversion is exact — deriving it here turns the
# single biggest clarifying-question group into clean rows.
_MASS_TO_TONNES = {
    "kg": 0.001,
    "kgs": 0.001,
    "tonne": 1.0,
    "tonnes": 1.0,
    "t": 1.0,
    "ton": 1.0,
    "tons": 1.0,
}
_FREIGHT_CATEGORIES = {"3.4", "3.9"}


def _derive_tonne_km(activity) -> float | None:
    """weight × distance for a transport row, or None if either is missing."""
    if activity.category_code not in _FREIGHT_CATEGORIES:
        return None
    factor = _MASS_TO_TONNES.get((activity.unit or "").strip().lower())
    raw = activity.raw_data or {}
    distance = raw.get("Distance_km") or raw.get("distance_km")
    if factor is None or activity.quantity is None or distance in (None, ""):
        return None
    try:
        return float(activity.quantity) * factor * float(str(distance).replace(",", ""))
    except (TypeError, ValueError):
        return None


@dataclass
class TemplateTable:
    """Minimal stand-in for RawTable so the staging loop can consume us."""

    sheet: str
    row_count: int
    detected_scope: int | None = None


def detect_template(content: bytes, filename: str) -> bool:
    """Cheap check: does this workbook carry the CLIMATRIX template sheet names?"""
    if not filename.lower().endswith(_XLSX_EXTENSIONS):
        return False
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        names = set(wb.sheetnames)
        wb.close()
    except Exception:
        return False
    return len(names & set(SHEET_CONFIGS.keys())) >= _MIN_TEMPLATE_SHEETS


def map_template(
    content: bytes, filename: str
) -> list[tuple[TemplateTable, list[MappedRow]]] | None:
    """Parse the template deterministically into the mapper's output shape.

    Returns None when parsing fails or yields nothing — the caller then falls
    back to the generic AI path, so a corrupted template still imports.
    """
    result = TemplateParser().parse(content, filename)
    if not result.success or result.total_activities == 0:
        return None

    out: list[tuple[TemplateTable, list[MappedRow]]] = []
    for sheet in result.sheets:
        rows: list[MappedRow] = []
        for a in sheet.activities:
            source = {str(k): _json_safe(v) for k, v in (a.raw_data or {}).items()}
            if a.activity_date:
                source.setdefault("activity_date", str(a.activity_date))
            if a.site:
                source.setdefault("site", str(a.site))

            quantity = float(a.quantity) if a.quantity is not None else None
            unit = a.unit
            tonne_km = _derive_tonne_km(a)
            if tonne_km is not None:
                source["derived"] = (
                    f"tonne-km = {a.quantity} {a.unit} × "
                    f"{source.get('Distance_km', source.get('distance_km'))} km"
                )
                quantity = round(tonne_km, 6)
                unit = "tonne-km"

            rows.append(
                MappedRow(
                    row_index=a.source_row,
                    activity_key=a.activity_key,
                    scope=a.scope,
                    category_code=a.category_code,
                    quantity=quantity,
                    unit=unit,
                    description=(a.description or "")[:500],
                    # Deterministic mapping — full self-confidence; grounding and
                    # the rule engine still verify against the real catalog.
                    llm_confidence=1.0,
                    question=None,
                    source=source,
                )
            )
        if rows:
            out.append(
                (
                    TemplateTable(
                        sheet=sheet.sheet_name,
                        row_count=sheet.total_rows,
                        detected_scope=sheet.scope,
                    ),
                    rows,
                )
            )
    return out or None
