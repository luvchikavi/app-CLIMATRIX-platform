"""Regression tests for unit parsing robustness (no DB, no LLM).

Real client files carry units as free text — including Hebrew abbreviations
whose gershayim (") crashes Pint's tokenizer if it reaches it raw. Any unit
Pint cannot parse must surface as UnitConversionError (the pipeline's readable
failure signal that grounding turns into a clarifying question), never as an
unhandled TokenError/500.
"""

from decimal import Decimal

import pytest

from app.services.calculation.normalizer import UnitConversionError, UnitNormalizer
from app.services.ingestion.grounding import check_unit


@pytest.fixture()
def normalizer():
    return UnitNormalizer()


def test_hebrew_kwh_alias(normalizer):
    # קוט"ש is the standard Hebrew abbreviation for kWh.
    result = normalizer.normalize(Decimal("100"), 'קוט"ש', "kWh")
    assert result.quantity == Decimal("100")
    assert result.conversion_applied is False


def test_hebrew_cubic_meter_alias(normalizer):
    result = normalizer.normalize(Decimal("5"), 'מ"ק', "m3")
    assert result.quantity == Decimal("5")


def test_hebrew_liter_alias_converts(normalizer):
    result = normalizer.normalize(Decimal("1000"), "ליטר", "gallons")
    assert result.conversion_applied is True
    assert result.quantity == pytest.approx(Decimal("264.17"), abs=Decimal("0.1"))


def test_unparseable_quoted_unit_raises_readable_error(normalizer):
    # A quote inside an unknown unit reaches Pint's tokenizer -> TokenError
    # unless the normalizer translates it.
    with pytest.raises(UnitConversionError):
        normalizer.normalize(Decimal("1"), 'ab"cd', "kWh")


def test_unparseable_unit_never_raises_token_error(normalizer):
    for bad in ('xx"yy', "kWh'", "50%(!)", "יח'"):
        with pytest.raises(UnitConversionError):
            normalizer.normalize(Decimal("1"), bad, "kg")


def test_alias_lookup_is_whitespace_and_case_tolerant(normalizer):
    result = normalizer.normalize(Decimal("2"), " Liters ", "liter")
    assert result.quantity == Decimal("2")
    assert result.conversion_applied is False


def test_check_unit_hebrew_kwh_is_convertible():
    ok, why = check_unit('קוט"ש', "kWh")
    assert ok is True


def test_check_unit_quoted_garbage_asks_instead_of_crashing():
    ok, why = check_unit('ab"cd', "kWh")
    assert ok is False
    assert "clarifying question" in why or "converted" in why
