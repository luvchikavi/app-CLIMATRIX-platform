"""
Tests for the CBAM screening service and the public /api/cbam/screen endpoint.

Covers the Omnibus 50 t cumulative de minimis (iron & steel, aluminium,
fertilisers, cement only), the hydrogen/electricity always-in-scope carve-out,
the 2026 10% default-value markup, and the ETS price fallback.
"""

from decimal import Decimal

import pytest

from app.services.cbam_screening import resolve_sector, screen_imports

# ============================================================================
# Service — sector resolution
# ============================================================================


def test_resolve_sector_from_cn_prefixes():
    assert resolve_sector("2523 21 00") == "cement"
    assert resolve_sector("7208") == "iron_steel"
    assert resolve_sector("73181500") == "iron_steel"
    assert resolve_sector("7601") == "aluminium"
    assert resolve_sector("3102") == "fertiliser"
    assert resolve_sector("2814") == "fertiliser"
    assert resolve_sector("2804") == "hydrogen"
    assert resolve_sector("2804 10 00") == "hydrogen"
    assert resolve_sector("2716") == "electricity"
    assert resolve_sector("9999") is None


def test_resolve_sector_from_names():
    assert resolve_sector("iron & steel") == "iron_steel"
    assert resolve_sector("Fertilisers") == "fertiliser"
    assert resolve_sector("hydrogen") == "hydrogen"


# ============================================================================
# Service — threshold logic
# ============================================================================


def test_under_threshold_is_exempt():
    result = screen_imports(
        [{"cn_code_or_sector": "iron_steel", "mass_kg": 30000}],
        ets_price_eur=Decimal("75"),
    )
    assert result["exempt"] is True
    assert result["in_threshold_mass_kg"] == 30000
    assert result["headroom_kg"] == 20000
    assert result["items"][0]["covered"] is False
    assert result["total_estimated_certificate_cost_eur"] == 0
    assert result["assumptions"]  # every result states its simplifications


def test_over_threshold_is_in_scope():
    result = screen_imports(
        [{"cn_code_or_sector": "iron_steel", "mass_kg": 60000}],
        ets_price_eur=Decimal("75"),
    )
    assert result["exempt"] is False
    assert result["headroom_kg"] == 0
    item = result["items"][0]
    assert item["covered"] is True
    # 60 t x 2.5 tCO2e/t x 1.10 markup = 165 tCO2e
    assert item["estimated_emissions_tco2e"] == pytest.approx(165.0)
    assert item["estimated_certificate_cost_eur"] == pytest.approx(165.0 * 75)


def test_hydrogen_always_covered_no_threshold():
    result = screen_imports(
        [
            {"cn_code_or_sector": "hydrogen", "mass_kg": 1000},
            {"cn_code_or_sector": "iron_steel", "mass_kg": 10000},
        ],
        ets_price_eur=Decimal("75"),
    )
    # Hydrogen does not count toward, nor benefit from, the 50 t threshold.
    assert result["in_threshold_mass_kg"] == 10000
    assert result["exempt"] is False
    hydrogen, steel = result["items"]
    assert hydrogen["covered"] is True
    assert hydrogen["counts_toward_threshold"] is False
    # 1 t x 12 tCO2e/t x 1.10 = 13.2 tCO2e
    assert hydrogen["estimated_emissions_tco2e"] == pytest.approx(13.2)
    assert steel["covered"] is False


def test_electricity_always_covered():
    result = screen_imports(
        [{"cn_code_or_sector": "electricity", "mass_kg": 500}],
        ets_price_eur=Decimal("75"),
    )
    assert result["exempt"] is False
    assert result["items"][0]["covered"] is True
    assert any("kWh" in a for a in result["assumptions"])


def test_mixed_basket_cumulative_threshold():
    """30 t steel + 25 t cement = 55 t cumulative -> both lines covered."""
    result = screen_imports(
        [
            {"cn_code_or_sector": "7208", "mass_kg": 30000},
            {"cn_code_or_sector": "2523", "mass_kg": 25000},
        ],
        ets_price_eur=Decimal("80"),
    )
    assert result["in_threshold_mass_kg"] == 55000
    assert result["exempt"] is False
    assert all(item["covered"] for item in result["items"])
    # Steel: 30 x 2.5 x 1.1 = 82.5; cement: 25 x 0.95 x 1.1 = 26.125
    assert result["total_estimated_emissions_tco2e"] == pytest.approx(108.625)
    assert result["total_estimated_certificate_cost_eur"] == pytest.approx(108.625 * 80)


def test_markup_10_percent_applied():
    result = screen_imports(
        [{"cn_code_or_sector": "aluminium", "mass_kg": 100000}],
        ets_price_eur=Decimal("75"),
    )
    assert result["default_value_markup_pct"] == 10.0
    # 100 t x 8.0 tCO2e/t = 800 base; +10% markup = 880
    assert result["items"][0]["estimated_emissions_tco2e"] == pytest.approx(880.0)


def test_unknown_line_is_out_of_scope_with_assumption():
    result = screen_imports(
        [
            {"cn_code_or_sector": "9999", "mass_kg": 999000},
            {"cn_code_or_sector": "cement", "mass_kg": 10000},
        ],
        ets_price_eur=Decimal("75"),
    )
    unknown = result["items"][0]
    assert unknown["sector"] is None
    assert unknown["covered"] is False
    # Unknown mass must not push the basket over the threshold.
    assert result["in_threshold_mass_kg"] == 10000
    assert result["exempt"] is True
    assert any("could not be mapped" in a for a in result["assumptions"])


# ============================================================================
# Endpoint — public /api/cbam/screen
# ============================================================================


@pytest.mark.asyncio
async def test_screen_endpoint_public_no_auth(client):
    resp = await client.post(
        "/api/cbam/screen",
        json={
            "items": [
                {"cn_code_or_sector": "7208", "mass_kg": 60000, "origin_country": "TR"}
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["exempt"] is False
    assert data["items"][0]["sector"] == "iron_steel"
    assert data["items"][0]["origin_country"] == "TR"
    # No EUETSPrice rows seeded -> €75 placeholder with an assumption.
    assert data["ets_price_eur"] == 75.0
    assert any("placeholder" in a for a in data["assumptions"])


@pytest.mark.asyncio
async def test_screen_endpoint_custom_ets_price(client):
    resp = await client.post(
        "/api/cbam/screen",
        json={
            "items": [{"cn_code_or_sector": "iron_steel", "mass_kg": 60000}],
            "ets_price_eur": 100,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ets_price_eur"] == 100.0
    # 60 x 2.5 x 1.1 = 165 tCO2e x €100
    assert data["total_estimated_certificate_cost_eur"] == pytest.approx(16500.0)


@pytest.mark.asyncio
async def test_screen_endpoint_uses_latest_db_ets_price(client, test_session):
    from datetime import date
    from uuid import uuid4

    from app.models.cbam import EUETSPrice

    for d, price in [
        (date(2026, 6, 24), Decimal("82.50")),
        (date(2026, 7, 1), Decimal("84.10")),
    ]:
        test_session.add(
            EUETSPrice(
                id=uuid4(),
                price_date=d,
                week_number=d.isocalendar()[1],
                year=d.year,
                price_eur=price,
            )
        )
    await test_session.commit()

    resp = await client.post(
        "/api/cbam/screen",
        json={"items": [{"cn_code_or_sector": "cement", "mass_kg": 60000}]},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ets_price_eur"] == 84.10


@pytest.mark.asyncio
async def test_screen_endpoint_rejects_empty_items(client):
    resp = await client.post("/api/cbam/screen", json={"items": []})
    assert resp.status_code == 422
