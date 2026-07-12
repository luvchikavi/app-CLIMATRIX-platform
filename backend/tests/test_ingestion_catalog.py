"""Unit tests for the factor-catalog retrieval index (anti-hallucination core).

Pure in-memory (no DB) so it's fast and CI-safe.
"""

from app.services.ingestion.catalog import (
    FactorCatalog,
    entry_from_record,
)

# A small representative slice of the real catalog.
_RECORDS = [
    ("electricity_il", 2, "2", "kWh", "IL"),
    ("electricity_uk", 2, "2", "kWh", "UK"),
    ("natural_gas_kwh", 1, "1.1", "kWh", "Global"),
    ("diesel_liters", 1, "1.1", "liters", "Global"),
    ("car_diesel_km", 1, "1.2", "km", "Global"),
    ("flight_long_business", 3, "3.6", "km", "Global"),
    ("flight_short_economy", 3, "3.6", "km", "Global"),
    ("commute_car_petrol", 3, "3.7", "km", "Global"),
    ("steel_purchased_kg", 3, "3.1", "kg", "Global"),
    ("waste_cardboard_recycled", 3, "3.5", "kg", "US"),
    ("hotel_night", 3, "3.6", "nights", "Global"),
]


def _catalog() -> FactorCatalog:
    return FactorCatalog([entry_from_record(*r) for r in _RECORDS])


def test_size_and_membership():
    cat = _catalog()
    assert len(cat) == len(_RECORDS)
    assert cat.is_real("electricity_il")
    assert not cat.is_real("totally_made_up_key")
    assert cat.get("diesel_liters").activity_unit == "liters"


def test_search_returns_real_keys_only():
    cat = _catalog()
    for hit in cat.search("some random office thing", top_n=5):
        assert cat.is_real(hit.activity_key)


def test_search_finds_expected_candidates():
    cat = _catalog()
    keys = lambda q, **k: [h.activity_key for h in cat.search(q, **k)]
    assert "steel_purchased_kg" in keys("purchased steel")
    assert "waste_cardboard_recycled" in keys("cardboard recycling")
    assert "hotel_night" in keys("hotel stays")
    # alias: "flights"/"air" -> flight
    assert any(k.startswith("flight_") for k in keys("business air travel"))
    # alias: "power" -> electricity
    assert any(k.startswith("electricity_") for k in keys("office power usage"))


def test_scope_filter():
    cat = _catalog()
    hits = cat.search("diesel", scope=1)
    assert hits and all(h.scope == 1 for h in hits)


def test_no_match_returns_empty():
    cat = _catalog()
    assert cat.search("xyzzy qwerty zzz") == []
