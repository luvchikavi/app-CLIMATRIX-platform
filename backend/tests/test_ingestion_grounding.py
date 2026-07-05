"""Unit tests for the deterministic unit-compatibility guard (no DB, no LLM)."""
from app.services.ingestion.grounding import check_unit


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
