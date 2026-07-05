"""Unit tests for the deterministic unit-compatibility guard (no DB, no LLM)."""

from app.services.ingestion.grounding import check_unit, classify_unit


def test_matching_units_ok():
    assert check_unit("kWh", "kWh")[0] is True
    assert check_unit("liters", "liters")[0] is True


def test_convertible_units_ok():
    # gallons -> liters is a safe linear conversion
    assert check_unit("gallons", "liters")[0] is True


def test_gas_volume_vs_energy_needs_question():
    # m3 <-> kWh needs a calorific value (NOT a linear conversion) -> must ask
    ok, why = check_unit("m3", "kWh")
    assert ok is False
    assert "convert" in why.lower() or "calorific" in why.lower()


def test_incompatible_dimensions_need_question():
    assert check_unit("km", "kg")[0] is False


def test_missing_unit_needs_question():
    assert check_unit("", "kWh")[0] is False
    assert check_unit("kWh", "")[0] is False


# --- spend-vs-physical enforcement -----------------------------------------


def test_classify_unit():
    assert classify_unit("USD") == "currency"
    assert classify_unit("€") == "currency"
    assert classify_unit("ILS") == "currency"
    assert classify_unit("kWh") == "physical"
    assert classify_unit("kg") == "physical"


def test_spend_value_on_physical_factor_asks():
    # Money value routed to a physical (kg) factor -> must ask, not auto-reconcile.
    ok, why = check_unit("USD", "kg")
    assert ok is False
    assert "spend" in why.lower() and "physical" in why.lower()


def test_physical_value_on_spend_factor_asks():
    ok, why = check_unit("kg", "USD")
    assert ok is False
    assert "spend-based" in why.lower() or "eeio" in why.lower()


def test_currency_to_currency_is_valid_spend():
    # EUR spend on a USD EEIO factor is fine — FX handled downstream.
    ok, why = check_unit("EUR", "USD")
    assert ok is True
    assert "spend" in why.lower() or "fx" in why.lower()
