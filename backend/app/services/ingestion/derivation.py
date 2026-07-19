"""Derived-Quantity Engine — the stage between activity-ID and grounding (§6).

Rows like "Flight TLV–JFK, 2 passengers" or "Raw material China → Haifa, 12 t"
carry no usable quantity in the factor's unit (pax-km, nights, tonne-km). This
stage derives one, honestly:

  * The LLM extracts ENTITIES ONLY — endpoints, explicit counts, explicit cabin
    or direction words, verbatim. It never computes, converts, or invents a
    number. ("Business trip" is a purpose, not a cabin class.)
  * Deterministic resolvers turn entities into quantities using bundled,
    versioned gazetteers (airports.csv, the transport route matrix) — every
    derived number is reproducible offline, no external APIs.
  * Every derived quantity lands on the data-quality ladder as ESTIMATED, with
    each assumption recorded on the row's audit trail plus the upgrade path a
    punch-list can chase.
  * Clarifying questions fire only where the assumption is materially
    significant: round-trip default (×2), long-haul cabin class (business
    ≈2.9×, first ≈4×), missing freight mass. Same-city airport choice (~2%)
    is recorded, never asked about.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

import anthropic

from app.config import get_settings
from app.data.airports import (
    AIRPORTS,
    GAZETTEER_VERSION,
    calculate_flight_distance,
    classify_flight_distance,
)
from app.data.transport_distances import TRANSPORT_DISTANCES

# DEFRA-recommended +9% uplift on great-circle distance for indirect routing.
GCD_UPLIFT = 1.09

# Units that already satisfy the target factor — rows carrying these need no derivation.
_DISTANCE_UNITS = {
    "km",
    "kilometer",
    "kilometers",
    "kilometre",
    "kilometres",
    "mi",
    "mile",
    "miles",
}
_NIGHT_UNITS = {"night", "nights"}
_TONNE_KM_UNITS = {"tonne-km", "tonne km", "tkm", "t-km", "ton-km", "tonne_km"}
_MASS_TO_TONNES = {
    "t": 1.0,
    "ton": 1.0,
    "tons": 1.0,
    "tonne": 1.0,
    "tonnes": 1.0,
    "mt": 1.0,
    "kg": 0.001,
    "kgs": 0.001,
}

# Freight keys expect tonne-km; the key itself already encodes the mode.
_FREIGHT_MODE_BY_KEY = {
    "road_freight_hgv": "road",
    "road_freight_van": "road",
    "road_freight_motorcycle": "road",
    "rail_freight": "rail",
    "sea_freight_container": "sea",
    "sea_freight_bulk": "sea",
    "air_freight": "air",
}

# The catalog carries short/long flight factors; domestic and medium map onto
# the nearest available band (recorded in provenance, immaterial vs asking).
_HAUL_TO_BAND = {
    "domestic": "short",
    "short": "short",
    "medium": "short",
    "long": "long",
}
_LONG_CLASS_KEYS = {
    "economy": "flight_long_economy",
    "business": "flight_long_business",
    "first": "flight_long_first",
}
_SHORT_CLASS_KEYS = {
    "economy": "flight_short_economy",
    "business": "flight_short_business",
}

# Principal airport for ambiguous multi-airport cities (normalized city name).
_CITY_PRIMARY = {
    "london": "LHR",
    "newyork": "JFK",
    "paris": "CDG",
    "tokyo": "HND",
    "moscow": "SVO",
    "milan": "MXP",
    "rome": "FCO",
    "istanbul": "IST",
    "saopaulo": "GRU",
    "shanghai": "PVG",
    "beijing": "PEK",
    "washington": "IAD",
    "chicago": "ORD",
    "houston": "IAH",
    "dubai": "DXB",
    "bangkok": "BKK",
    "osaka": "KIX",
    "telaviv": "TLV",
    "berlin": "BER",
    "stockholm": "ARN",
    "oslo": "OSL",
    "buenosaires": "EZE",
    "toronto": "YYZ",
    "montreal": "YUL",
    "seoul": "ICN",
    "jakarta": "CGK",
    "johannesburg": "JNB",
    "melbourne": "MEL",
    "frankfurt": "FRA",
}

# Principal international gateway per country (ISO2) — used when a row names
# only a country ("Israel → Germany"). Coarse, recorded as an assumption.
_COUNTRY_PRIMARY = {
    "IL": "TLV",
    "US": "JFK",
    "GB": "LHR",
    "DE": "FRA",
    "FR": "CDG",
    "IT": "FCO",
    "ES": "MAD",
    "NL": "AMS",
    "BE": "BRU",
    "CH": "ZRH",
    "AT": "VIE",
    "PL": "WAW",
    "CZ": "PRG",
    "PT": "LIS",
    "GR": "ATH",
    "IE": "DUB",
    "DK": "CPH",
    "SE": "ARN",
    "NO": "OSL",
    "FI": "HEL",
    "TR": "IST",
    "AE": "DXB",
    "SA": "RUH",
    "QA": "DOH",
    "JO": "AMM",
    "EG": "CAI",
    "MA": "CMN",
    "ZA": "JNB",
    "KE": "NBO",
    "NG": "LOS",
    "CN": "PVG",
    "HK": "HKG",
    "JP": "HND",
    "KR": "ICN",
    "TW": "TPE",
    "SG": "SIN",
    "TH": "BKK",
    "VN": "SGN",
    "MY": "KUL",
    "ID": "CGK",
    "PH": "MNL",
    "IN": "DEL",
    "AU": "SYD",
    "NZ": "AKL",
    "CA": "YYZ",
    "MX": "MEX",
    "BR": "GRU",
    "AR": "EZE",
    "CL": "SCL",
    "CO": "BOG",
    "RU": "SVO",
    "UA": "KBP",
    "RO": "OTP",
    "HU": "BUD",
    "CY": "LCA",
}

# Common country names (normalized) -> ISO2. Covers what shows up in real
# travel/freight sheets; anything unresolved becomes a clarifying question
# through the normal flow, never a guess.
_COUNTRY_NAME_TO_ISO2 = {
    "israel": "IL",
    "usa": "US",
    "unitedstates": "US",
    "unitedstatesofamerica": "US",
    "america": "US",
    "uk": "GB",
    "unitedkingdom": "GB",
    "greatbritain": "GB",
    "england": "GB",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
    "netherlands": "NL",
    "holland": "NL",
    "belgium": "BE",
    "switzerland": "CH",
    "austria": "AT",
    "poland": "PL",
    "czechia": "CZ",
    "czechrepublic": "CZ",
    "portugal": "PT",
    "greece": "GR",
    "ireland": "IE",
    "denmark": "DK",
    "sweden": "SE",
    "norway": "NO",
    "finland": "FI",
    "turkey": "TR",
    "uae": "AE",
    "unitedarabemirates": "AE",
    "dubai": "AE",
    "saudiarabia": "SA",
    "qatar": "QA",
    "jordan": "JO",
    "egypt": "EG",
    "morocco": "MA",
    "southafrica": "ZA",
    "kenya": "KE",
    "nigeria": "NG",
    "china": "CN",
    "hongkong": "HK",
    "japan": "JP",
    "southkorea": "KR",
    "korea": "KR",
    "taiwan": "TW",
    "singapore": "SG",
    "thailand": "TH",
    "vietnam": "VN",
    "malaysia": "MY",
    "indonesia": "ID",
    "philippines": "PH",
    "india": "IN",
    "australia": "AU",
    "newzealand": "NZ",
    "canada": "CA",
    "mexico": "MX",
    "brazil": "BR",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
    "russia": "RU",
    "ukraine": "UA",
    "romania": "RO",
    "hungary": "HU",
    "cyprus": "CY",
}

_IATA_RE = re.compile(r"^[A-Za-z]{3}$")
_ISO2_RE = re.compile(r"^[A-Za-z]{2}$")


def _norm_place(text: str) -> str:
    return re.sub(r"[^a-z]", "", (text or "").lower())


# City index over the bundled gazetteer, built once on first use.
_CITY_INDEX: dict[str, list[str]] | None = None


def _city_index() -> dict[str, list[str]]:
    global _CITY_INDEX
    if _CITY_INDEX is None:
        idx: dict[str, list[str]] = {}
        for code, (_name, city, _country, _lat, _lon) in AIRPORTS.items():
            idx.setdefault(_norm_place(city), []).append(code)
        _CITY_INDEX = idx
    return _CITY_INDEX


@dataclass
class Endpoint:
    iata: str
    method: str  # iata_code | city | city_primary | country_primary

    @property
    def country(self) -> str | None:
        data = AIRPORTS.get(self.iata)
        return data[2] if data else None


def resolve_endpoint(text: str | None) -> Endpoint | None:
    """Resolve free text ("TLV", "Tel Aviv", "Israel", "IL") to an airport.

    Deterministic against the bundled gazetteer — an unresolvable endpoint
    returns None and the row falls back to the normal question flow.
    """
    t = (text or "").strip()
    if not t:
        return None
    if _IATA_RE.match(t) and t.upper() in AIRPORTS:
        return Endpoint(t.upper(), "iata_code")

    norm = _norm_place(t)
    if not norm:
        return None

    # Country first — by name, then by a bare ISO2 code.
    iso2 = _COUNTRY_NAME_TO_ISO2.get(norm)
    if iso2 is None and _ISO2_RE.match(t) and t.upper() in _COUNTRY_PRIMARY:
        iso2 = t.upper()
    if iso2 and iso2 in _COUNTRY_PRIMARY:
        return Endpoint(_COUNTRY_PRIMARY[iso2], "country_primary")

    codes = _city_index().get(norm)
    if codes:
        primary = _CITY_PRIMARY.get(norm)
        if primary and primary in codes:
            return Endpoint(primary, "city_primary")
        # Same-city airport choice is immaterial (~2%) — deterministic pick.
        return Endpoint(sorted(codes)[0], "city")
    return None


def resolve_country(text: str | None) -> str | None:
    """Free text -> ISO2, via country name, bare code, or a city's country."""
    t = (text or "").strip()
    if not t:
        return None
    norm = _norm_place(t)
    if norm in _COUNTRY_NAME_TO_ISO2:
        return _COUNTRY_NAME_TO_ISO2[norm]
    if _ISO2_RE.match(t):
        return t.upper()
    ep = resolve_endpoint(t)
    return ep.country if ep else None


# =============================================================================
# ENTITY EXTRACTION (the only LLM touch — entities, never numbers)
# =============================================================================

_ENTITY_TOOL = {
    "name": "extract_travel_entities",
    "description": (
        "Extract travel/freight entities from each row EXACTLY as written. "
        "Never compute, convert, infer, or invent anything."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "rows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "kind": {
                            "type": "string",
                            "enum": ["flight", "hotel", "freight", "other"],
                        },
                        "origin_text": {
                            "type": ["string", "null"],
                            "description": "Origin exactly as written (airport code, city, country). Null if absent.",
                        },
                        "destination_text": {"type": ["string", "null"]},
                        "direction": {
                            "type": "string",
                            "enum": ["round_trip", "one_way", "unspecified"],
                            "description": "ONLY from explicit words: 'round trip'/'return'/'RT' vs 'one way'/'single'. Otherwise unspecified.",
                        },
                        "cabin_class": {
                            "type": ["string", "null"],
                            "enum": [
                                "economy",
                                "premium_economy",
                                "business",
                                "first",
                                None,
                            ],
                            "description": "ONLY explicit cabin wording ('business class', 'economy'). 'Business trip'/'business travel' is a PURPOSE, not a cabin — null.",
                        },
                        "travelers": {
                            "type": ["integer", "null"],
                            "description": "Explicit traveler/passenger count written in the row, else null.",
                        },
                        "trips": {
                            "type": ["integer", "null"],
                            "description": "Explicit number of trips/flights written in the row ('4 flights', 'x2'), else null.",
                        },
                        "nights": {
                            "type": ["integer", "null"],
                            "description": "Explicit hotel nights written in the row, else null.",
                        },
                        "stay_location_text": {
                            "type": ["string", "null"],
                            "description": "Hotel stay city/country exactly as written, else null.",
                        },
                        "mass_value": {
                            "type": ["number", "null"],
                            "description": "Explicit shipped mass NUMBER written in the row, verbatim, else null.",
                        },
                        "mass_unit": {
                            "type": ["string", "null"],
                            "description": "The mass unit as written ('t', 'kg', 'tonnes'), else null.",
                        },
                        "bare_number_role": {
                            "type": "string",
                            "enum": [
                                "trips",
                                "travelers",
                                "distance_km",
                                "nights",
                                "mass",
                                "spend",
                                "unknown",
                            ],
                            "description": "What the row's bare quantity value (given per row) most likely represents, judged from the row text alone.",
                        },
                    },
                    "required": ["id", "kind", "direction", "bare_number_role"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["rows"],
        "additionalProperties": False,
    },
}

_EXTRACT_SYSTEM = (
    "You extract travel and freight ENTITIES from spreadsheet rows for an "
    "emissions inventory. Rules:\n"
    "- Extract ONLY what is explicitly written. Never compute, convert, infer, "
    "or fill in what 'must be' true.\n"
    "- 'Business trip' / 'business travel' names the PURPOSE of travel, not a "
    "cabin class. cabin_class is null unless the text names the cabin itself.\n"
    "- direction comes only from explicit words (round trip / return / RT vs "
    "one way / single). Anything else is 'unspecified'.\n"
    "- Numbers: copy explicit counts verbatim (travelers, trips, nights, mass). "
    "Never derive one number from another.\n"
    "- Each row shows its bare quantity cell value; classify what that number "
    "represents in bare_number_role — do not use it for anything else."
)

_EXTRACT_CHUNK = 80


@dataclass
class TravelEntities:
    kind: str = "other"
    origin_text: str | None = None
    destination_text: str | None = None
    direction: str = "unspecified"
    cabin_class: str | None = None
    travelers: int | None = None
    trips: int | None = None
    nights: int | None = None
    stay_location_text: str | None = None
    mass_value: float | None = None
    mass_unit: str | None = None
    bare_number_role: str = "unknown"


def extract_entities(
    items: list[dict], client=None, context=None
) -> dict[int, TravelEntities]:
    """One fast-model call per <=80 rows: row text -> entities. items are
    {"id": row_index, "text": ..., "quantity": ...}."""
    settings = get_settings()
    client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)
    system = _EXTRACT_SYSTEM
    if context is not None:
        system = f"{context.prompt_block()}\n\n{system}"

    out: dict[int, TravelEntities] = {}
    for start in range(0, len(items), _EXTRACT_CHUNK):
        chunk = items[start : start + _EXTRACT_CHUNK]
        user = "Rows (id | bare quantity cell | text):\n" + "\n".join(
            f'- id={it["id"]} | quantity={it.get("quantity")} | {it["text"]}'
            for it in chunk
        )
        msg = client.messages.create(
            model=settings.claude_model_fast or settings.claude_model,
            max_tokens=4000,
            system=system,
            tools=[_ENTITY_TOOL],
            tool_choice={"type": "tool", "name": "extract_travel_entities"},
            messages=[{"role": "user", "content": user}],
        )
        payload = next(b.input for b in msg.content if b.type == "tool_use")
        for row in payload.get("rows", []):
            try:
                rid = int(row.get("id"))
            except (TypeError, ValueError):
                continue
            ent = TravelEntities(
                kind=row.get("kind") or "other",
                origin_text=row.get("origin_text"),
                destination_text=row.get("destination_text"),
                direction=row.get("direction") or "unspecified",
                cabin_class=row.get("cabin_class"),
                travelers=_pos_int(row.get("travelers")),
                trips=_pos_int(row.get("trips")),
                nights=_pos_int(row.get("nights")),
                stay_location_text=row.get("stay_location_text"),
                mass_value=_pos_float(row.get("mass_value")),
                mass_unit=row.get("mass_unit"),
                bare_number_role=row.get("bare_number_role") or "unknown",
            )
            out[rid] = ent
    return out


def _pos_int(v) -> int | None:
    try:
        i = int(v)
        return i if 0 < i <= 10_000 else None
    except (TypeError, ValueError):
        return None


def _pos_float(v) -> float | None:
    try:
        f = float(v)
        return f if 0 < f <= 1e9 else None
    except (TypeError, ValueError):
        return None


# =============================================================================
# DETERMINISTIC RESOLVERS
# =============================================================================


@dataclass
class Derivation:
    quantity: float | None
    unit: str | None
    activity_key: str | None  # refined key, or None = keep the mapper's
    region: str | None  # stay country for hotels -> country-specific factor
    assumptions: list[str] = field(default_factory=list)
    state: dict = field(default_factory=dict)  # -> provenance["derivation"]
    questions: list[dict] = field(default_factory=list)


_UPGRADE_FLIGHT = (
    "ESTIMATED: distance derived from the route, not ticketed. Provide the "
    "itinerary/ticketed distance to upgrade this row to CALCULATED."
)
_UPGRADE_HOTEL = (
    "ESTIMATED: average per-night factor. Provide hotel invoices or a "
    "supplier-specific factor to upgrade this row."
)
_UPGRADE_FREIGHT = (
    "ESTIMATED: distance from the bundled country-pair route matrix. Provide "
    "shipment documents (actual route + mass) to upgrade this row to CALCULATED."
)

_RT_QUESTION = {
    "group_key": "derived:round_trip",
    "field": "quantity",
    "question": (
        "Flights without an explicit direction were treated as ROUND TRIPS "
        "(distance ×2 — the usual case for business travel). Keep round-trip, "
        "or switch these to one-way?"
    ),
    "choices": [
        {"value": "round_trip", "label": "Round trips — keep ×2"},
        {"value": "one_way", "label": "One-way — halve the distance"},
    ],
}


def _multiplier_from_bare(m_quantity, role: str, wanted: str) -> int | None:
    """Use the row's bare number as a trip/traveler count only when the
    extractor classified it as such and it looks like a small count."""
    if role != wanted or m_quantity is None:
        return None
    try:
        q = float(m_quantity)
    except (TypeError, ValueError):
        return None
    if q.is_integer() and 0 < q <= 50:
        return int(q)
    return None


def derive_flight(ent: TravelEntities, m_quantity=None) -> Derivation | None:
    if ent.bare_number_role == "distance_km" and m_quantity:
        return None  # the file's number IS a distance — nothing to derive
    origin = resolve_endpoint(ent.origin_text)
    dest = resolve_endpoint(ent.destination_text)
    if origin is None or dest is None or origin.iata == dest.iata:
        return None
    gcd = calculate_flight_distance(origin.iata, dest.iata)
    if not gcd:
        return None

    one_way = gcd * GCD_UPLIFT
    haul = classify_flight_distance(gcd, origin.iata, dest.iata)
    band = _HAUL_TO_BAND[haul]

    rt_assumed = ent.direction == "unspecified"
    round_trip = ent.direction != "one_way"
    trips = (
        ent.trips
        or _multiplier_from_bare(m_quantity, ent.bare_number_role, "trips")
        or 1
    )
    travelers = (
        ent.travelers
        or _multiplier_from_bare(m_quantity, ent.bare_number_role, "travelers")
        or 1
    )
    quantity = round(one_way * (2 if round_trip else 1) * trips * travelers, 1)

    cabin_assumed = ent.cabin_class not in ("economy", "business", "first")
    cabin = ent.cabin_class if not cabin_assumed else "economy"
    class_keys = _LONG_CLASS_KEYS if band == "long" else _SHORT_CLASS_KEYS
    activity_key = class_keys.get(cabin) or class_keys["economy"]

    assumptions = [
        (
            f"Distance derived: {origin.iata}→{dest.iata} great-circle "
            f"{gcd:,.0f} km × {GCD_UPLIFT} routing uplift = {one_way:,.0f} km "
            f"one-way (gazetteer {GAZETTEER_VERSION})."
        )
    ]
    if origin.method != "iata_code":
        assumptions.append(
            f'Origin "{ent.origin_text}" resolved to {origin.iata} ({origin.method}).'
        )
    if dest.method != "iata_code":
        assumptions.append(
            f'Destination "{ent.destination_text}" resolved to {dest.iata} ({dest.method}).'
        )
    if rt_assumed:
        assumptions.append("Treated as a round trip (×2) — industry default, confirm.")
    else:
        assumptions.append(
            "Round trip (×2) per row text." if round_trip else "One-way per row text."
        )
    if trips > 1 or travelers > 1:
        assumptions.append(f"×{trips} trip(s) × {travelers} traveler(s) applied.")
    if haul != band:
        assumptions.append(
            f"Haul '{haul}' mapped to the '{band}'-haul factor (nearest available)."
        )
    if cabin_assumed:
        assumptions.append(
            "Cabin class assumed economy pending confirmation (business ≈2.9×, first ≈4×)."
            if band == "long"
            else "Cabin class assumed economy (short-haul — class impact limited)."
        )
    assumptions.append(_UPGRADE_FLIGHT)

    questions: list[dict] = []
    if rt_assumed:
        questions.append(dict(_RT_QUESTION))
    if band == "long" and cabin_assumed:
        questions.append(
            {
                "group_key": f"derived:class:{origin.iata}-{dest.iata}",
                "field": "activity",
                "question": (
                    f"Long-haul flights {origin.iata}→{dest.iata}: which cabin "
                    f"class? (business ≈2.9× economy, first ≈4×)"
                ),
                "choices": [
                    {
                        "value": _LONG_CLASS_KEYS["economy"],
                        "label": "Economy (default)",
                    },
                    {
                        "value": _LONG_CLASS_KEYS["business"],
                        "label": "Business (≈2.9×)",
                    },
                    {"value": _LONG_CLASS_KEYS["first"], "label": "First (≈4×)"},
                ],
            }
        )

    state = {
        "engine": "flight",
        "gazetteer": GAZETTEER_VERSION,
        "origin": origin.iata,
        "destination": dest.iata,
        "gcd_km": round(gcd, 1),
        "uplift": GCD_UPLIFT,
        "one_way_km": round(one_way, 1),
        "round_trip": round_trip,
        "rt_assumed": rt_assumed,
        "trips": trips,
        "travelers": travelers,
        "haul": haul,
        "cabin": cabin,
        "cabin_assumed": cabin_assumed,
        "assumptions": assumptions,
    }
    return Derivation(
        quantity=quantity,
        unit="km",
        activity_key=activity_key,
        region=None,
        assumptions=assumptions,
        state=state,
        questions=questions,
    )


def derive_hotel(ent: TravelEntities, m_quantity=None) -> Derivation | None:
    nights = ent.nights or _multiplier_from_bare(
        m_quantity, ent.bare_number_role, "nights"
    )
    if not nights:
        return None
    travelers = ent.travelers or 1
    quantity = float(nights * travelers)
    region = resolve_country(ent.stay_location_text)

    assumptions = [
        f"Hotel nights derived: {nights} night(s) × {travelers} traveler(s)."
    ]
    if region:
        assumptions.append(
            f"Stay country {region} — country-specific hotel factor applies."
        )
    else:
        assumptions.append("Stay country unknown — global-average hotel factor used.")
    assumptions.append(_UPGRADE_HOTEL)

    state = {
        "engine": "hotel",
        "nights": nights,
        "travelers": travelers,
        "stay_country": region,
        "assumptions": assumptions,
    }
    return Derivation(
        quantity=quantity,
        unit="nights",
        activity_key="hotel_night",
        region=region,
        assumptions=assumptions,
        state=state,
        questions=[],
    )


def _route_km(route: dict, mode: str) -> float | None:
    by_mode = {
        "sea": route.get("sea_distance_km"),
        "air": route.get("air_distance_km"),
        "rail": route.get("rail_distance_km"),
        "road": route.get("total_distance_km"),
    }
    km = by_mode.get(mode) or route.get("total_distance_km")
    try:
        km = float(km)
    except (TypeError, ValueError):
        return None
    return km if km > 0 else None


def derive_freight(
    ent: TravelEntities, activity_key: str, m_quantity=None, m_unit: str | None = None
) -> Derivation | None:
    mode = _FREIGHT_MODE_BY_KEY.get(activity_key)
    if mode is None:
        return None
    o_iso = resolve_country(ent.origin_text)
    d_iso = resolve_country(ent.destination_text)
    if not o_iso or not d_iso or o_iso == d_iso:
        return None
    route = TRANSPORT_DISTANCES.get((o_iso, d_iso))
    reversed_route = False
    if route is None:
        route = TRANSPORT_DISTANCES.get((d_iso, o_iso))
        reversed_route = route is not None
    if route is None:
        return None
    km = _route_km(route, mode)
    if km is None:
        return None

    # Mass: from the row's unit column (t/kg), or explicit in the text.
    mass_tonnes: float | None = None
    unit_norm = (m_unit or "").strip().lower()
    if unit_norm in _MASS_TO_TONNES and m_quantity:
        try:
            mass_tonnes = float(m_quantity) * _MASS_TO_TONNES[unit_norm]
        except (TypeError, ValueError):
            mass_tonnes = None
    if mass_tonnes is None and ent.mass_value:
        factor = _MASS_TO_TONNES.get((ent.mass_unit or "").strip().lower(), None)
        if factor is not None:
            mass_tonnes = ent.mass_value * factor
    if mass_tonnes is None:
        role_mass = ent.bare_number_role == "mass"
        if role_mass and m_quantity:
            try:
                mass_tonnes = float(m_quantity)  # bare number judged to be tonnes
            except (TypeError, ValueError):
                mass_tonnes = None

    assumptions = [
        (
            f"Route {o_iso}→{d_iso} ({mode}): {km:,.0f} km from the bundled "
            f"route matrix ({route.get('source', 'route matrix')})"
            + (" — reverse-direction entry." if reversed_route else ".")
        )
    ]
    state = {
        "engine": "freight_route",
        "origin_country": o_iso,
        "destination_country": d_iso,
        "mode": mode,
        "route_km": round(km, 1),
        "reversed_route": reversed_route,
    }

    if mass_tonnes is not None:
        quantity = round(mass_tonnes * km, 1)
        assumptions.append(f"tonne-km = {mass_tonnes:g} t × {km:,.0f} km.")
        assumptions.append(_UPGRADE_FREIGHT)
        state.update({"mass_tonnes": mass_tonnes, "assumptions": assumptions})
        return Derivation(
            quantity=quantity,
            unit="tonne-km",
            activity_key=None,
            region=None,
            assumptions=assumptions,
            state=state,
            questions=[],
        )

    # No mass anywhere -> ask ONCE (grouped); the answer completes the tonne-km.
    assumptions.append(
        "Shipped mass unknown — asked once; without it this stays a gap "
        "(or use the spend amount via an EEIO freight-spend activity, PCAF 4-5)."
    )
    state.update({"mass_tonnes": None, "assumptions": assumptions})
    question = {
        "group_key": f"derived:mass:{o_iso}-{d_iso}:{activity_key}",
        "field": "quantity",
        "question": (
            f"Freight {o_iso}→{d_iso} ({mode}): what is the total shipped mass "
            f"in tonnes? (Without it we can only estimate from spend — PCAF 4-5.)"
        ),
        "choices": [
            {"value": "no_mass", "label": "No mass data — leave as a gap / use spend"}
        ],
    }
    return Derivation(
        quantity=None,
        unit=None,
        activity_key=None,
        region=None,
        assumptions=assumptions,
        state=state,
        questions=[question],
    )


# =============================================================================
# STAGE ORCHESTRATION (called from the ingestion orchestrator)
# =============================================================================


def derivation_kind(m) -> str | None:
    """Does this mapped row need a derived quantity? Returns the engine kind."""
    key = m.activity_key or ""
    unit_norm = (m.unit or "").strip().lower()
    unit_defaulted = bool(getattr(m, "unit_defaulted", False))
    if key.startswith("flight_"):
        if m.quantity is None or unit_defaulted or unit_norm not in _DISTANCE_UNITS:
            return "flight"
    elif key == "hotel_night":
        if m.quantity is None or unit_defaulted or unit_norm not in _NIGHT_UNITS:
            return "hotel"
    elif key == "travel_spend_hotel":
        # Mapped to the SPEND key but the file carried no money unit — if the
        # text names nights, the physical method wins the hierarchy and the
        # derivation re-keys the row to hotel_night.
        if m.quantity is None or unit_defaulted:
            return "hotel"
    elif key in _FREIGHT_MODE_BY_KEY:
        if (
            m.quantity is None
            or unit_defaulted
            or unit_norm in _MASS_TO_TONNES
            or unit_norm not in _TONNE_KM_UNITS
        ):
            return "freight"
    return None


def _row_text(m) -> str:
    parts = [m.description or ""]
    src = m.source or {}
    extra = " ".join(
        str(v) for v in src.values() if v not in (None, "") and str(v) not in parts[0]
    )
    if extra:
        parts.append(extra[:300])
    return " | ".join(p for p in parts if p)[:500]


def derive_for_rows(mapped_rows, client=None, context=None) -> dict:
    """The derived-quantity stage: pick candidate rows, extract entities (one
    fast-model call), resolve deterministically. Returns {row_index: Derivation}.
    Rows that don't resolve simply fall through to the normal question flow."""
    candidates = [(m, derivation_kind(m)) for m in mapped_rows]
    candidates = [(m, k) for m, k in candidates if k]
    if not candidates:
        return {}

    items = [
        {"id": m.row_index, "text": _row_text(m), "quantity": m.quantity}
        for m, _ in candidates
    ]
    try:
        entities = extract_entities(items, client=client, context=context)
    except Exception:
        return {}  # extraction failure must never break the parse

    out: dict = {}
    for m, kind in candidates:
        ent = entities.get(m.row_index)
        if ent is None:
            continue
        try:
            if kind == "flight" and ent.kind in ("flight", "other"):
                d = derive_flight(ent, m.quantity)
            elif kind == "hotel" and ent.kind in ("hotel", "other"):
                d = derive_hotel(ent, m.quantity)
            elif kind == "freight" and ent.kind in ("freight", "other"):
                d = derive_freight(ent, m.activity_key, m.quantity, m.unit)
            else:
                d = None
        except Exception:
            d = None
        if d is not None:
            out[m.row_index] = d
    return out


def apply_derivation_to_mapped(m, d: Derivation, cat) -> None:
    """Write a derivation onto the in-flight MappedRow before grounding."""
    if d.quantity is not None:
        m.quantity = d.quantity
        m.unit = d.unit
    if d.activity_key and cat.is_real(d.activity_key):
        entry = cat.get(d.activity_key)
        m.activity_key = d.activity_key
        if entry:
            m.scope = entry.scope
            m.category_code = entry.category_code


def stamp_derived_verdict(verdict, d: Derivation) -> None:
    """A derived quantity is honest but ESTIMATED — never better, per the ladder.
    The assumptions ride the row's audit-trail reasons."""
    verdict.pcaf_data_quality = max(verdict.pcaf_data_quality or 4, 4)
    if d.quantity is not None and verdict.tier not in ("gap",):
        verdict.tier = "estimated"
    verdict.reasons = list(verdict.reasons) + list(d.assumptions)


def apply_derivation_answer(row, state: dict, answer: str) -> bool:
    """Handle an answer to a derivation question deterministically from the
    stored state. Returns True if the answer was consumed."""
    # Never mutate the ORM-loaded dict: SQLAlchemy's change detection compares
    # the flush-time value against its loaded snapshot BY EQUALITY, and mutating
    # the snapshot's own nested dict makes the change invisible (no UPDATE).
    state = copy.deepcopy(state)
    engine = state.get("engine")
    answer = (answer or "").strip()

    if engine == "flight" and answer in ("round_trip", "one_way"):
        rt = answer == "round_trip"
        try:
            qty = (
                float(state["one_way_km"])
                * (2 if rt else 1)
                * int(state.get("trips") or 1)
                * int(state.get("travelers") or 1)
            )
        except (KeyError, TypeError, ValueError):
            return False
        row.quantity = round(qty, 1)
        state["round_trip"] = rt
        state["rt_assumed"] = False
        state["assumptions"] = [
            a
            for a in (state.get("assumptions") or [])
            if "round trip (×2) — industry default" not in a.lower()
        ] + [
            (
                "Round trip (×2) confirmed by client."
                if rt
                else "One-way confirmed by client."
            )
        ]
        _restamp_state(row, state)
        return True

    if engine == "freight_route":
        if answer == "no_mass":
            state["mass_declined"] = True
            _restamp_state(row, state)
            return True
        try:
            mass = float(answer.replace(",", ""))
        except (TypeError, ValueError):
            return False
        if mass <= 0:
            return False
        row.quantity = round(mass * float(state["route_km"]), 1)
        row.unit = "tonne-km"
        state["mass_tonnes"] = mass
        state["assumptions"] = (state.get("assumptions") or []) + [
            f"tonne-km = {mass:g} t (client-provided) × {state['route_km']:,.0f} km.",
            _UPGRADE_FREIGHT,
        ]
        _restamp_state(row, state)
        return True

    return False


def _restamp_state(row, state: dict) -> None:
    # Reassign (not mutate) so SQLAlchemy notices the JSON column change.
    prov = dict(row.provenance or {})
    prov["derivation"] = state
    row.provenance = prov
