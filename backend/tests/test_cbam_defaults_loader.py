"""
Tests for the CBAM default-values file loader and the DB-preference
resolution in the screening service.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from app.services.cbam_defaults_loader import (
    DefaultValuesParseError,
    parse_default_values_file,
)
from app.services.cbam_screening import resolve_default_intensity, screen_imports

FIXTURE_CSV = """CN code,Country of origin,Direct SEE (tCO2e/t),Indirect SEE (tCO2e/t),Total SEE (tCO2e/t),Year
7208,TR,2.10,0.30,2.40,2026
7208,,2.30,0.40,2.70,2026
2523 21 00,CN,0.80,,0.80,2026
not-a-code,XX,,,,
7601,IN,10.5,1.5,,2026
"""


@pytest.fixture
def fixture_csv(tmp_path: Path) -> Path:
    path = tmp_path / "cbam_defaults_fixture.csv"
    path.write_text(FIXTURE_CSV, encoding="utf-8")
    return path


def test_parse_default_values_csv(fixture_csv: Path):
    rows = parse_default_values_file(fixture_csv)
    # The "not-a-code" row is skipped (no digits)
    assert len(rows) == 4

    tr = rows[0]
    assert tr["cn_code"] == "7208"
    assert tr["country_code"] == "TR"
    assert tr["sector"] == "iron_steel"
    assert tr["direct_see"] == Decimal("2.10")
    assert tr["indirect_see"] == Decimal("0.30")
    assert tr["total_see"] == Decimal("2.40")
    assert tr["dataset_year"] == 2026

    any_country = rows[1]
    assert any_country["country_code"] is None
    assert any_country["total_see"] == Decimal("2.70")

    cement = rows[2]
    assert cement["cn_code"] == "25232100"  # digits only, spaces stripped
    assert cement["sector"] == "cement"
    assert cement["indirect_see"] is None

    # Total derived from direct + indirect when the column is blank
    alu = rows[3]
    assert alu["total_see"] == Decimal("12.0")


def test_parse_rejects_file_without_cn_header(tmp_path: Path):
    path = tmp_path / "bad.csv"
    path.write_text("foo,bar\n1,2\n", encoding="utf-8")
    with pytest.raises(DefaultValuesParseError):
        parse_default_values_file(path)


def test_parse_rejects_unknown_extension(tmp_path: Path):
    path = tmp_path / "bad.txt"
    path.write_text("CN code\n7208\n", encoding="utf-8")
    with pytest.raises(DefaultValuesParseError):
        parse_default_values_file(path)


# ============================================================================
# Screening resolution: CN x country > CN > sector representative
# ============================================================================

DB_ROWS = [
    {
        "cn_code": "7208",
        "country_code": "TR",
        "total_see": "2.40",
        "source": "commission_2026",
    },
    {
        "cn_code": "7208",
        "country_code": None,
        "total_see": "2.70",
        "source": "commission_2026",
    },
    {
        "cn_code": "72",
        "country_code": None,
        "total_see": "2.5",
        "source": "representative_v0",
    },
]


def test_resolve_prefers_cn_and_country():
    intensity, source = resolve_default_intensity(
        "7208 10 00", "TR", "iron_steel", DB_ROWS
    )
    assert intensity == Decimal("2.40")
    assert source == "commission_2026"


def test_resolve_falls_back_to_cn_without_country():
    intensity, _ = resolve_default_intensity("72081000", "IN", "iron_steel", DB_ROWS)
    assert intensity == Decimal("2.70")


def test_resolve_falls_back_to_sector_representative():
    # No DB rows at all -> hardcoded sector value
    intensity, source = resolve_default_intensity("7601", "IN", "aluminium", None)
    assert intensity == Decimal("8.0")
    assert source == "representative_v0"


def test_screen_imports_uses_db_default_values():
    result = screen_imports(
        [{"cn_code_or_sector": "7208", "mass_kg": 60000, "origin_country": "TR"}],
        ets_price_eur=Decimal("100"),
        default_values=DB_ROWS,
    )
    item = result["items"][0]
    assert item["covered"] is True
    assert item["intensity_source"] == "commission_2026"
    # 60 t x 2.40 x 1.10 markup = 158.4 tCO2e
    assert item["estimated_emissions_tco2e"] == pytest.approx(158.4)
    assert result["total_estimated_certificate_cost_eur"] == pytest.approx(15840.0)
    assert any("commission_2026" in a for a in result["assumptions"])
