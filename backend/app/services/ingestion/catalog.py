"""Factor catalog retrieval index — the anti-hallucination core of the parser.

The AI mapper is only ever allowed to choose an ``activity_key`` from candidates
returned by this index, so it can never invent a key that isn't a real emission
factor. Pure lexical search over the live 386-key catalog — stdlib only, no LLM,
no external deps — so it's cheap, deterministic, and testable.

Replaces the stale ~40-key hardcoded list that used to live in the LLM prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(s: str) -> set[str]:
    return set(_TOKEN.findall((s or "").lower()))


# Everyday words a client might use -> tokens that appear in catalog keys.
ALIASES: dict[str, str] = {
    "power": "electricity",
    "grid": "electricity",
    "kwh": "electricity",
    "elec": "electricity",
    "mains": "electricity",
    "gas": "natural_gas",
    "ng": "natural_gas",
    "gasoline": "petrol",
    "benzine": "petrol",
    "flights": "flight",
    "air": "flight",
    "airfare": "flight",
    "plane": "flight",
    "commuting": "commute",
    "commuter": "commute",
    "recycling": "recycled",
    "landfilled": "landfill",
    "trash": "waste",
    "aluminium": "aluminum",
    "shipping": "freight",
    "haulage": "freight",
    "logistics": "freight",
    "hotels": "hotel",
    "accommodation": "hotel",
    "lodging": "hotel",
    "fuel": "diesel",
    "vehicle": "car",
    "fleet": "car",
    "van": "van",
    "cloud": "electricity",
    "server": "electricity",
    "datacenter": "electricity",
}

# Measurement-unit words: intent hints (kwh → electricity via ALIASES) but weak
# discriminators between candidate keys.
_UNIT_TOKENS = {
    "kwh",
    "mwh",
    "gj",
    "liters",
    "litres",
    "liter",
    "litre",
    "gallons",
    "gallon",
    "kg",
    "tonnes",
    "tons",
    "tonne",
    "ton",
    "km",
    "miles",
    "mile",
    "m3",
    "nights",
    "usd",
    "eur",
    "ils",
    "gbp",
}

# Region codes -> country name tokens, so "electricity Israel" finds the IL grid key.
_REGION_NAMES: dict[str, str] = {
    "IL": "israel",
    "US": "usa united states america",
    "UK": "uk britain united kingdom",
    "GB": "uk britain united kingdom",
    "DE": "germany",
    "FR": "france",
    "ES": "spain",
    "IT": "italy",
    "NL": "netherlands",
    "PL": "poland",
    "EU": "europe european",
    "CN": "china",
    "IN": "india",
    "JP": "japan",
    "AU": "australia",
    "CA": "canada",
    "BR": "brazil",
    "TR": "turkey",
    "ZA": "south africa",
    "MX": "mexico",
}


@dataclass
class FactorEntry:
    activity_key: str
    scope: int
    category_code: str
    activity_unit: str
    region: str
    display_name: str
    tokens: set[str] = field(default_factory=set)

    def score(self, q_tokens: set[str]) -> float:
        if not q_tokens:
            return 0.0
        # Unit words (kwh, liters, km…) signal intent but shouldn't discriminate
        # between keys: weighting them like real words made verbose Scope-3 keys
        # ("downstream_leased_electricity_kwh") outrank the plain grid key.
        overlap = sum(
            0.5 if t in _UNIT_TOKENS else 2.0 for t in (q_tokens & self.tokens)
        )
        substring = sum(
            1
            for t in q_tokens
            if len(t) >= 3 and t not in _UNIT_TOKENS and t in self.activity_key
        )
        return overlap + substring


class FactorCatalog:
    """Searchable index of the emission-factor catalog."""

    def __init__(self, entries: list[FactorEntry]):
        self.entries = entries
        self._by_key = {e.activity_key: e for e in entries}

    def __len__(self) -> int:
        return len(self.entries)

    def get(self, activity_key: str) -> FactorEntry | None:
        return self._by_key.get(activity_key)

    def is_real(self, activity_key: str) -> bool:
        return activity_key in self._by_key

    def search(
        self,
        query: str,
        top_n: int = 15,
        scope: int | None = None,
        region: str | None = None,
    ) -> list[FactorEntry]:
        """Return the top-N candidate factors for a free-text query (a column
        header, description, or the LLM's guess). Optionally constrain by scope.

        When the organization's region is known, factors for THAT region are
        boosted (and Global fallbacks slightly) — an Israeli org typing
        "electricity" should be offered the IL grid key first, not an
        alphabetical parade of other countries."""
        q = _tokens(query)
        q |= {ALIASES[t] for t in list(q) if t in ALIASES}
        pool = (e for e in self.entries if scope is None or e.scope == scope)

        def ranked(e: FactorEntry) -> float:
            base = e.score(q)
            if base <= 0:
                return 0.0
            if region and e.region == region:
                return base + 2.5
            if e.region == "Global":
                return base + 0.5
            return base

        scored = [(ranked(e), e) for e in pool]
        scored = [(s, e) for s, e in scored if s > 0]
        scored.sort(key=lambda x: (-x[0], x[1].activity_key))
        return [e for _, e in scored[:top_n]]


def entry_from_record(
    activity_key: str,
    scope,
    category_code: str,
    activity_unit: str,
    region: str,
    description: str = "",
) -> FactorEntry:
    # `description` here is the DB display_name (e.g. "Israel Grid") — carries the
    # real name + country, so tokenize it for search and use it as the display name.
    display = (description or "").strip() or activity_key.replace("_", " ").title()
    toks = (
        _tokens(activity_key)
        | _tokens(category_code)
        | _tokens(description)
        | _tokens(display)
        | _tokens(_REGION_NAMES.get((region or "").upper(), ""))
    )
    try:
        scope_int = int(scope)
    except (TypeError, ValueError):
        scope_int = 0
    return FactorEntry(
        activity_key=activity_key,
        scope=scope_int,
        category_code=category_code or "",
        activity_unit=activity_unit or "",
        region=region or "Global",
        display_name=display,
        tokens=toks,
    )


async def build_from_db(session) -> FactorCatalog:
    """Build the index from the live emission_factors table (the authoritative catalog)."""
    from sqlalchemy import text

    # Include display_name — it carries the real-world name/country (e.g. "Israel Grid")
    # so a search for "electricity Israel" can find electricity_il.
    rows = (
        await session.execute(
            text(
                "SELECT DISTINCT activity_key, scope, category_code, activity_unit, "
                "region, display_name "
                "FROM emission_factors WHERE activity_key IS NOT NULL"
            )
        )
    ).all()
    entries = [entry_from_record(*r) for r in rows]
    return FactorCatalog(entries)


# Lazy module-level singleton (built once per process from the DB).
_catalog: FactorCatalog | None = None


async def get_catalog(session) -> FactorCatalog:
    global _catalog
    if _catalog is None:
        _catalog = await build_from_db(session)
    return _catalog
