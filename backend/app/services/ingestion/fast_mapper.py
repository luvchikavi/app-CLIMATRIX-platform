"""Fast mapper — the "deterministic-first, LLM-assist" strategy (WS1).

The original mapper sends every row to the LLM, which is slow and can time out on
big multi-sheet files. This mapper is much faster with the same grounding safety:

  1. detect_columns()  — ONE LLM call per sheet identifies which column holds the
     activity, the quantity, the unit, the date. (A recognised CLIMATRIX template
     skips even this.)
  2. extract rows deterministically using that column map.
  3. map_distinct()    — ONE LLM call per sheet maps the sheet's DISTINCT activity
     values to real catalog keys (a 180-row transport sheet usually has ~10 distinct
     activities). The mapping is then applied to every row with no further LLM cost.

So a sheet costs ~2 LLM calls regardless of row count, versus one-call-per-40-rows
before. Output is a list[MappedRow] — a drop-in replacement for map_table(), so the
grounding / rules / confidence / staging pipeline downstream is unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import anthropic

from app.config import get_settings
from app.services.ingestion.catalog import FactorCatalog
from app.services.ingestion.loader import RawTable
from app.services.ingestion.mapper import (
    MappedRow,
    _is_empty_row,
    _is_placeholder,
    _is_sample_row,
    _json_safe,
)

_COLUMN_TOOL = {
    "name": "identify_columns",
    "description": "Identify the role of each column in a sustainability data sheet.",
    "input_schema": {
        "type": "object",
        "properties": {
            "activity_column": {
                "type": ["string", "null"],
                "description": "Column name holding WHAT was consumed/purchased (fuel, material, item, activity type). Null if the item name is spread across several columns.",
            },
            "quantity_column": {
                "type": ["string", "null"],
                "description": "Column holding the numeric amount.",
            },
            "unit_column": {
                "type": ["string", "null"],
                "description": "Column holding the unit or currency (kWh, liters, kg, USD…).",
            },
            "date_column": {"type": ["string", "null"]},
            "description_column": {
                "type": ["string", "null"],
                "description": "Free-text description/notes column, if any.",
            },
        },
        "required": ["activity_column", "quantity_column", "unit_column"],
        "additionalProperties": False,
    },
}

_DISTINCT_TOOL = {
    "name": "map_activities",
    "description": "Map each distinct activity description to a canonical CLIMATRIX activity key.",
    "input_schema": {
        "type": "object",
        "properties": {
            "mappings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "activity_text": {"type": "string"},
                        "activity_key": {
                            "type": ["string", "null"],
                            "description": "EXACTLY one of the candidate keys, or null if none fit / unsure.",
                        },
                        "confidence": {"type": "number"},
                        "question": {
                            "type": ["string", "null"],
                            "description": "A short clarifying question if unsure, else null.",
                        },
                    },
                    "required": ["activity_text", "activity_key", "confidence"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["mappings"],
        "additionalProperties": False,
    },
}


@dataclass
class ColumnMap:
    activity: str | None
    quantity: str | None
    unit: str | None
    date: str | None = None
    description: str | None = None


def _clean_rows(table: RawTable) -> list[dict]:
    return [
        r
        for r in table.rows
        if not _is_empty_row(r) and not _is_placeholder(r) and not _is_sample_row(r)
    ]


def detect_columns(table: RawTable, client, settings) -> ColumnMap:
    """One LLM call: figure out which column is activity / quantity / unit / date."""
    sample = _clean_rows(table)[:8]
    payload = [{k: _json_safe(v) for k, v in r.items()} for r in sample]
    system = (
        "You are given a spreadsheet of sustainability/emissions data. Identify the "
        "role of each column so the rows can be read programmatically. Use the EXACT "
        "column names from the header."
    )
    user = (
        f"Sheet: {table.sheet}\nColumns: {table.columns}\n"
        f"Sample rows (JSON):\n{json.dumps(payload, default=str)}"
    )
    msg = client.messages.create(
        model=settings.claude_model_fast or settings.claude_model,
        max_tokens=500,
        system=system,
        tools=[_COLUMN_TOOL],
        tool_choice={"type": "tool", "name": "identify_columns"},
        messages=[{"role": "user", "content": user}],
    )
    out = next(b.input for b in msg.content if b.type == "tool_use")
    cols = set(table.columns)

    def pick(name):
        v = out.get(name)
        return v if v in cols else None

    return ColumnMap(
        activity=pick("activity_column"),
        quantity=pick("quantity_column"),
        unit=pick("unit_column"),
        date=pick("date_column"),
        description=pick("description_column"),
    )


def _activity_text(row: dict, cmap: ColumnMap) -> str:
    """The text used to identify the activity for a row. Prefers the activity column;
    falls back to concatenating the row's non-numeric text so nothing is lost."""
    if cmap.activity and row.get(cmap.activity) not in (None, ""):
        base = str(row[cmap.activity]).strip()
        if cmap.description and row.get(cmap.description):
            base = f"{base} — {row[cmap.description]}"
        return base
    parts = [
        str(v).strip()
        for k, v in row.items()
        if isinstance(v, str)
        and len(str(v).strip()) > 1
        and not str(k).startswith("Unnamed:")
    ]
    return " ".join(parts)


def _num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _candidates_for_texts(
    catalog: FactorCatalog,
    table: RawTable,
    texts: list[str],
    per: int = 6,
    cap: int = 120,
):
    seen: dict = {}
    for e in catalog.search(f"{table.sheet} {' '.join(table.columns)}", top_n=12):
        seen[e.activity_key] = e
    for t in texts:
        for e in catalog.search(t, top_n=per):
            seen[e.activity_key] = e
    return list(seen.values())[:cap]


def map_distinct(
    distinct: list[str], catalog: FactorCatalog, table: RawTable, client, settings
) -> dict:
    """One LLM call: map distinct activity texts -> catalog keys. Returns {text: dict}."""
    cands = _candidates_for_texts(catalog, table, distinct)
    cand_keys = {c.activity_key for c in cands}
    cand_block = "\n".join(
        f"- {c.activity_key} | Scope {c.scope}.{c.category_code} | expects {c.activity_unit} | {c.display_name}"
        for c in cands
    )
    system = (
        "Map each distinct client activity description to EXACTLY one candidate key "
        "below, or null if none truly fits / you're unsure — never invent a key. Read "
        "the sheet name for context (e.g. a 'Scope2_Electricity' sheet is electricity).\n\n"
        f"Sheet: {table.sheet}\nCANDIDATE KEYS:\n{cand_block}"
    )
    user = "Distinct activities to map:\n" + json.dumps(distinct, default=str)
    # Use the FAST model — distinct-value mapping is a constrained pick from the
    # candidate list, and grounding + human review catch any misses. This is the
    # main speed lever (Opus here made a 29-distinct sheet take ~26s).
    msg = client.messages.create(
        model=settings.claude_model_fast or settings.claude_model,
        max_tokens=4000,
        system=system,
        tools=[_DISTINCT_TOOL],
        tool_choice={"type": "tool", "name": "map_activities"},
        messages=[{"role": "user", "content": user}],
    )
    out = next(b.input for b in msg.content if b.type == "tool_use")
    result = {}
    for m in out.get("mappings", []):
        key = m.get("activity_key")
        if key and (key not in cand_keys and not catalog.is_real(key)):
            key = None
        result[m.get("activity_text", "")] = {
            "key": key,
            "confidence": float(m.get("confidence", 0.5)),
            "question": m.get("question"),
        }
    return result


def map_table_fast(
    table: RawTable,
    catalog: FactorCatalog,
    max_rows: int | None = None,
    client: anthropic.Anthropic | None = None,
) -> list[MappedRow]:
    """Drop-in replacement for map_table(): ~2 LLM calls per sheet regardless of size."""
    settings = get_settings()
    client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)

    rows = _clean_rows(table)
    if max_rows:
        rows = rows[:max_rows]
    if not rows:
        return []

    # 1) column roles (1 call)
    cmap = detect_columns(table, client, settings)

    # 2) extract deterministically + collect distinct activity texts
    extracted = []
    for i, r in enumerate(rows):
        text = _activity_text(r, cmap)
        qty = _num(r.get(cmap.quantity)) if cmap.quantity else None
        unit = (
            str(r.get(cmap.unit)).strip()
            if cmap.unit and r.get(cmap.unit) is not None
            else None
        )
        extracted.append((i, r, text, qty, unit))

    distinct = sorted({e[2] for e in extracted if e[2]})
    key_map = (
        map_distinct(distinct, catalog, table, client, settings) if distinct else {}
    )

    # 3) apply the distinct mapping to every row (no further LLM cost)
    out: list[MappedRow] = []
    for i, r, text, qty, unit in extracted:
        m = key_map.get(text, {})
        key = m.get("key")
        entry = catalog.get(key) if key else None
        out.append(
            MappedRow(
                row_index=i,
                activity_key=key,
                scope=entry.scope if entry else None,
                category_code=entry.category_code if entry else None,
                quantity=qty,
                unit=unit or (entry.activity_unit if entry else None),
                description=text[:500],
                llm_confidence=float(m.get("confidence", 0.5)),
                question=m.get("question"),
                source={str(k): _json_safe(v) for k, v in r.items()},
            )
        )
    return out
