"""Unit tests for the compliance rule engine (no DB, no LLM)."""
from app.services.ingestion.catalog import FactorCatalog, entry_from_record
from app.services.ingestion.rule_engine import (
    check_row,
    is_cbam_good,
    scope_category_consistent,
)

_CATALOG = FactorCatalog(
    [
        entry_from_record("natural_gas_kwh", 1, "1.1", "kWh", "Global"),
        entry_from_record("electricity_il", 2, "2", "kWh", "IL"),
        entry_from_record("flight_long_business", 3, "3.6", "km", "Global"),
        entry_from_record("commute_car_petrol", 3, "3.7", "km", "Global"),
        entry_from_record("steel_purchased_kg", 3, "3.1", "kg", "Global"),
    ]
)


def test_cbam_tagging():
    assert is_cbam_good("steel_purchased_kg")
    assert is_cbam_good("aluminum_primary_purchased_kg")
    assert not is_cbam_good("flight_long_business")


def test_scope_category_prefix_consistency():
    assert scope_category_consistent(3, "3.6")
    assert not scope_category_consistent(1, "3.6")
    assert scope_category_consistent(2, "2")


def test_clean_row_has_no_violations():
    assert check_row(_CATALOG, "flight_long_business", 3, "3.6") == []


def test_wrong_scope_on_fuel_flagged():
    # gas combustion is Scope 1, not Scope 2
    v = check_row(_CATALOG, "natural_gas_kwh", 2, "2")
    assert any(x.rule == "scope_mismatch" for x in v)
    assert any(x.suggested_scope == 1 for x in v)


def test_flight_filed_as_commuting_flagged():
    # flights are 3.6, not 3.7 (commuting)
    v = check_row(_CATALOG, "flight_long_business", 3, "3.7")
    assert any(x.rule == "category_mismatch" for x in v)
    assert any(x.suggested_category == "3.6" for x in v)


def test_inconsistent_scope_category_flagged():
    v = check_row(_CATALOG, "steel_purchased_kg", 1, "3.1")
    assert any(x.rule == "scope_category_inconsistent" for x in v)


def test_unknown_key_no_rule_violations():
    # unknown keys are the grounding layer's job, not the rule engine's
    assert check_row(_CATALOG, "made_up_key", 3, "3.6") == []
