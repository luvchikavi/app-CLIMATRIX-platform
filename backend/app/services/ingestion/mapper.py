"""LLM mapper — the semantic brain of the ingestion layer.

Proposes a canonical mapping for each source row, but choosing ``activity_key``
ONLY from real catalog candidates surfaced by retrieval (never invents one). The
deterministic grounding / rule / confidence layers then validate + score every
pick, and anything unsure becomes a clarifying question. This is what turns
"keyword guessing" into "semantic understanding": the model reads the full row +
sheet + column context and picks the correct candidate.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import anthropic

from app.config import get_settings
from app.services.ingestion.catalog import FactorCatalog
from app.services.ingestion.loader import RawTable

_PLACEHOLDERS = {"[dropdown]", "[number]", "[paste/type]", "[optional]", "[date]", "[text]"}

_MAP_TOOL = {
    "name": "map_rows",
    "description": "Map each source data row to a canonical CLIMATRIX activity.",
    "input_schema": {
        "type": "object",
        "properties": {
            "rows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "row_index": {"type": "integer"},
                        "activity_key": {
                            "type": ["string", "null"],
                            "description": "EXACTLY one of the provided candidate keys, or null if none fit or you are unsure.",
                        },
                        "quantity": {"type": ["number", "null"]},
                        "unit": {"type": ["string", "null"]},
                        "description": {"type": "string"},
                        "confidence": {"type": "number", "description": "0..1 self-assessment"},
                        "question": {
                            "type": ["string", "null"],
                            "description": "A short, targeted clarifying question if unsure (unit, which activity, spend vs physical), else null.",
                        },
                    },
                    "required": ["row_index", "activity_key", "confidence"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["rows"],
        "additionalProperties": False,
    },
}


@dataclass
class MappedRow:
    row_index: int
    activity_key: str | None
    scope: int | None
    category_code: str | None
    quantity: float | None
    unit: str | None
    description: str
    llm_confidence: float
    question: str | None
    source: dict


def _is_placeholder(row: dict) -> bool:
    vals = [str(v).strip().lower() for v in row.values() if v is not None]
    return bool(vals) and all(v in _PLACEHOLDERS or v == "" for v in vals)


def _json_safe(v):
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def _candidates(catalog: FactorCatalog, table: RawTable, k: int = 35):
    text = f"{table.sheet} {' '.join(table.columns)}"
    for r in table.rows[:10]:
        for v in r.values():
            if isinstance(v, str) and v.strip().lower() not in _PLACEHOLDERS and len(v) > 2:
                text += " " + v
    return catalog.search(text, top_n=k)


def map_table(
    table: RawTable,
    catalog: FactorCatalog,
    max_rows: int | None = None,
    client: anthropic.Anthropic | None = None,
) -> list[MappedRow]:
    """Map a RawTable's rows to canonical activities via grounded LLM tool-use.
    Scope/category are taken from the catalog entry of the chosen key (not the LLM),
    so they are always internally consistent with the real factor."""
    settings = get_settings()
    client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)

    cands = _candidates(catalog, table)
    cand_keys = {c.activity_key for c in cands}
    cand_block = "\n".join(
        f"- {c.activity_key} | Scope {c.scope}.{c.category_code} | expects {c.activity_unit} | {c.display_name}"
        for c in cands
    )

    rows = [r for r in table.rows if not _is_placeholder(r)]
    if max_rows:
        rows = rows[:max_rows]
    payload = [
        {"row_index": i, **{k: _json_safe(v) for k, v in r.items()}}
        for i, r in enumerate(rows)
    ]

    system = (
        "You map messy client sustainability data to CLIMATRIX emission activities.\n"
        "RULES:\n"
        "1. For each row, choose activity_key EXACTLY from the candidate list below, "
        "or null if none truly fits or you're unsure — never invent a key.\n"
        "2. Read the FULL context: the sheet name, the column names, and the row values "
        "together (e.g. 'Steel sheets from a supplier' on a 'Purchased Goods' sheet is "
        "purchased steel, not electricity).\n"
        "3. Pull quantity + unit from the row. If the unit is ambiguous or the row is "
        "spend-only with no physical quantity, set activity_key you're confident about "
        "but add a targeted clarifying question.\n"
        "4. confidence is your honest 0..1 self-assessment.\n\n"
        f"CANDIDATE KEYS (choose only from these):\n{cand_block}"
    )
    user = (
        f"Sheet: {table.sheet}\nColumns: {table.columns}\n"
        f"Rows (JSON):\n{json.dumps(payload, default=str)}"
    )

    msg = client.messages.create(
        model=settings.claude_model,
        max_tokens=8000,
        system=system,
        tools=[_MAP_TOOL],
        tool_choice={"type": "tool", "name": "map_rows"},
        messages=[{"role": "user", "content": user}],
    )
    tool_input = next(b.input for b in msg.content if b.type == "tool_use")

    out: list[MappedRow] = []
    for m in tool_input.get("rows", []):
        idx = m.get("row_index", 0)
        key = m.get("activity_key")
        # Reject anything that isn't a real, offered candidate -> becomes a question.
        if key and (key not in cand_keys and not catalog.is_real(key)):
            key = None
        entry = catalog.get(key) if key else None
        out.append(
            MappedRow(
                row_index=idx,
                activity_key=key,
                scope=entry.scope if entry else None,
                category_code=entry.category_code if entry else None,
                quantity=m.get("quantity"),
                unit=m.get("unit"),
                description=str(m.get("description", "")),
                llm_confidence=float(m.get("confidence", 0.5)),
                question=m.get("question") if not key else m.get("question"),
                source=rows[idx] if idx < len(rows) else {},
            )
        )
    return out
