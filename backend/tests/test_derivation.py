"""Derived-Quantity Engine tests.

Covers: deterministic resolvers (flight / hotel / freight), the entity
extractor's parsing (fake client), the upgraded airports gazetteer, the
RF / 3.6-dispatch calculation fixes, and the orchestrator integration
(derive → stage ESTIMATED → answer → commit with country factor).
"""

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.data.airports import (
    AIRPORTS,
    calculate_flight_distance,
    search_airports,
)
from app.models.emission import Activity, Emission, EmissionFactor
from app.models.ingestion import (
    ClarificationQuestion,
    IngestionSession,
    RowStatus,
    StagedRow,
)
from app.services.calculation import ActivityInput, CalculationPipeline
from app.services.ingestion import derivation, orchestrator
from app.services.ingestion.derivation import (
    GCD_UPLIFT,
    TravelEntities,
    apply_derivation_answer,
    derivation_kind,
    derive_flight,
    derive_freight,
    derive_hotel,
    extract_entities,
    resolve_country,
    resolve_endpoint,
)
from app.services.ingestion.mapper import MappedRow

# =============================================================================
# Gazetteer (bundled OpenFlights snapshot)
# =============================================================================


def test_gazetteer_size_and_key_airports():
    assert len(AIRPORTS) > 5000
    for code in ("TLV", "JFK", "LHR", "ETM", "HFA", "SIN", "GRU", "NBO"):
        assert code in AIRPORTS


def test_gazetteer_distance_tlv_jfk():
    d = calculate_flight_distance("TLV", "JFK")
    assert d == pytest.approx(9117, abs=60)


def test_search_ranks_exact_code_first():
    assert search_airports("TLV", 3)[0]["iata_code"] == "TLV"
    london = [a["iata_code"] for a in search_airports("london", 5)]
    assert "LHR" in london


# =============================================================================
# Endpoint / country resolution
# =============================================================================


def test_resolve_endpoint_iata_city_country():
    assert resolve_endpoint("TLV").iata == "TLV"
    assert resolve_endpoint("Tel Aviv").iata == "TLV"
    assert resolve_endpoint("London").iata == "LHR"
    assert resolve_endpoint("Israel").iata == "TLV"
    assert resolve_endpoint("DE").iata == "FRA"
    assert resolve_endpoint("Atlantis") is None
    assert resolve_endpoint(None) is None


def test_resolve_country():
    assert resolve_country("Israel") == "IL"
    assert resolve_country("china") == "CN"
    assert resolve_country("IL") == "IL"
    assert resolve_country("Paris") == "FR"  # via the city's airport
    assert resolve_country("nowhereland") is None


# =============================================================================
# Flight resolver
# =============================================================================


def _flight_ent(**kw):
    base = dict(kind="flight", origin_text="TLV", destination_text="JFK")
    base.update(kw)
    return TravelEntities(**base)


def test_flight_round_trip_default_with_questions():
    d = derive_flight(_flight_ent())
    gcd = calculate_flight_distance("TLV", "JFK")
    assert d.quantity == pytest.approx(gcd * GCD_UPLIFT * 2, abs=0.11)
    assert d.unit == "km"
    assert d.activity_key == "flight_long_economy"
    groups = {q["group_key"] for q in d.questions}
    assert groups == {"derived:round_trip", "derived:class:TLV-JFK"}
    assert any("round trip" in a.lower() for a in d.assumptions)
    assert d.state["rt_assumed"] is True


def test_flight_explicit_one_way_business_no_questions():
    d = derive_flight(_flight_ent(direction="one_way", cabin_class="business"))
    gcd = calculate_flight_distance("TLV", "JFK")
    assert d.quantity == pytest.approx(gcd * GCD_UPLIFT, abs=0.11)
    assert d.activity_key == "flight_long_business"
    assert d.questions == []


def test_flight_travelers_from_bare_number():
    d = derive_flight(_flight_ent(bare_number_role="travelers"), m_quantity=2)
    gcd = calculate_flight_distance("TLV", "JFK")
    assert d.quantity == pytest.approx(gcd * GCD_UPLIFT * 2 * 2, rel=1e-6)
    assert d.state["travelers"] == 2


def test_flight_short_haul_no_class_question():
    d = derive_flight(
        TravelEntities(kind="flight", origin_text="LHR", destination_text="CDG")
    )
    assert d.activity_key == "flight_short_economy"
    groups = {q["group_key"] for q in d.questions}
    assert groups == {"derived:round_trip"}  # class question is long-haul only


def test_flight_israel_international_is_long_haul():
    # TLV-LHR is ~3,588 km ("medium" by distance) but Israel international
    # flights always take the long-haul factor.
    d = derive_flight(_flight_ent(destination_text="LHR"))
    assert d.activity_key == "flight_long_economy"


def test_flight_distance_km_role_skips_derivation():
    assert derive_flight(_flight_ent(bare_number_role="distance_km"), 9000) is None


def test_flight_unresolvable_endpoint_returns_none():
    assert derive_flight(_flight_ent(origin_text="Atlantis")) is None


def test_flight_rt_answer_recompute():
    d = derive_flight(_flight_ent(travelers=2))
    row = SimpleNamespace(
        quantity=d.quantity, unit="km", provenance={"derivation": d.state}
    )
    assert apply_derivation_answer(row, d.state, "one_way") is True
    gcd = calculate_flight_distance("TLV", "JFK")
    assert row.quantity == pytest.approx(gcd * GCD_UPLIFT * 2, rel=1e-4)  # ×2 travelers
    assert row.provenance["derivation"]["round_trip"] is False


# =============================================================================
# Hotel resolver
# =============================================================================


def test_hotel_nights_travelers_country():
    d = derive_hotel(
        TravelEntities(kind="hotel", nights=3, travelers=2, stay_location_text="Israel")
    )
    assert d.quantity == 6.0
    assert d.unit == "nights"
    assert d.activity_key == "hotel_night"
    assert d.region == "IL"
    assert d.questions == []


def test_hotel_without_nights_returns_none():
    assert derive_hotel(TravelEntities(kind="hotel")) is None


def test_spend_hotel_rekeys_to_physical_nights():
    # Mapper picked the spend key but the file had no money unit — nights in
    # the text win the method hierarchy and re-key the row to hotel_night.
    m = _mapped("travel_spend_hotel", 3, "USD", defaulted=True)
    assert derivation_kind(m) == "hotel"
    d = derive_hotel(
        TravelEntities(
            kind="hotel", nights=3, travelers=2, stay_location_text="Berlin"
        ),
        m.quantity,
    )
    assert d.activity_key == "hotel_night"
    assert d.quantity == 6.0
    assert d.region == "DE"  # Berlin -> its airport's country


def test_spend_hotel_with_real_money_unit_untouched():
    assert derivation_kind(_mapped("travel_spend_hotel", 4000, "USD")) is None


# =============================================================================
# Freight resolver
# =============================================================================


def test_freight_mass_times_route():
    d = derive_freight(
        TravelEntities(kind="freight", origin_text="China", destination_text="Israel"),
        "sea_freight_container",
        m_quantity=12,
        m_unit="t",
    )
    assert d.quantity == pytest.approx(12 * 12000, rel=1e-6)  # CN->IL sea 12,000 km
    assert d.unit == "tonne-km"
    assert d.questions == []


def test_freight_reverse_route_lookup():
    # The matrix has CN->US but no US->CN entry — the reverse lookup covers it.
    d = derive_freight(
        TravelEntities(kind="freight", origin_text="USA", destination_text="China"),
        "sea_freight_container",
        m_quantity=1,
        m_unit="t",
    )
    assert d is not None and d.state["reversed_route"] is True


def test_freight_missing_mass_asks_once_then_answer_completes():
    d = derive_freight(
        TravelEntities(kind="freight", origin_text="China", destination_text="Israel"),
        "sea_freight_container",
    )
    assert d.quantity is None
    assert len(d.questions) == 1 and d.questions[0]["field"] == "quantity"

    row = SimpleNamespace(quantity=None, unit=None, provenance={"derivation": d.state})
    assert apply_derivation_answer(row, d.state, "8.5") is True
    assert row.quantity == pytest.approx(8.5 * 12000, rel=1e-6)
    assert row.unit == "tonne-km"


def test_freight_awaiting_mass_clears_defaulted_quantity():
    # "Air freight Israel to Germany",1 with no unit column: the mapper
    # defaults unit to tonne-km, but the bare 1 is NOT tonne-km. Until the
    # mass answer arrives the row must hold NO quantity and read as a gap.
    from app.services.ingestion.derivation import (
        apply_derivation_to_mapped,
        stamp_derived_verdict,
    )

    d = derive_freight(
        TravelEntities(
            kind="freight", origin_text="Israel", destination_text="Germany"
        ),
        "air_freight",
    )
    assert d.quantity is None
    m = _mapped("air_freight", 1, "tonne-km", defaulted=True)
    fake_cat = SimpleNamespace(is_real=lambda k: False, get=lambda k: None)
    apply_derivation_to_mapped(m, d, fake_cat)
    assert m.quantity is None and m.unit is None

    verdict = SimpleNamespace(pcaf_data_quality=3, tier="calculated", reasons=[])
    stamp_derived_verdict(verdict, d)
    assert verdict.tier == "gap"
    assert verdict.pcaf_data_quality == 4


def test_freight_no_mass_answer_stays_gap():
    d = derive_freight(
        TravelEntities(kind="freight", origin_text="China", destination_text="Israel"),
        "sea_freight_container",
    )
    row = SimpleNamespace(quantity=None, unit=None, provenance={"derivation": d.state})
    assert apply_derivation_answer(row, d.state, "no_mass") is True
    assert row.quantity is None
    assert row.provenance["derivation"]["mass_declined"] is True


# =============================================================================
# Candidate detection (which rows enter the stage)
# =============================================================================


def _mapped(key, qty, unit, defaulted=False):
    return MappedRow(0, key, 3, "3.6", qty, unit, "d", 0.9, None, {}, defaulted)


def test_derivation_kind_triggers():
    assert derivation_kind(_mapped("flight_long_economy", 2, "km", True)) == "flight"
    assert derivation_kind(_mapped("flight_long_economy", None, None)) == "flight"
    assert derivation_kind(_mapped("flight_long_economy", 9000, "km")) is None
    assert derivation_kind(_mapped("hotel_night", 3, "nights")) is None
    assert derivation_kind(_mapped("hotel_night", 3, "nights", True)) == "hotel"
    assert derivation_kind(_mapped("sea_freight_container", 12, "t")) == "freight"
    assert derivation_kind(_mapped("sea_freight_container", 1000, "tonne-km")) is None
    assert derivation_kind(_mapped("electricity_kwh", None, None)) is None


# =============================================================================
# Entity extractor (fake client — no API)
# =============================================================================


class _FakeMessages:
    def __init__(self, payload):
        self._payload = payload

    def create(self, **kwargs):
        block = SimpleNamespace(type="tool_use", input=self._payload)
        return SimpleNamespace(content=[block])


def test_extract_entities_parses_tool_payload():
    payload = {
        "rows": [
            {
                "id": 0,
                "kind": "flight",
                "origin_text": "TLV",
                "destination_text": "JFK",
                "direction": "unspecified",
                "cabin_class": None,
                "travelers": 2,
                "bare_number_role": "unknown",
            }
        ]
    }
    fake_client = SimpleNamespace(messages=_FakeMessages(payload))
    out = extract_entities(
        [{"id": 0, "text": "Flight TLV-JFK 2 pax", "quantity": None}],
        client=fake_client,
    )
    assert out[0].origin_text == "TLV" and out[0].travelers == 2
    assert out[0].cabin_class is None  # "business trip" trap: purpose, not cabin


# =============================================================================
# Calculation fixes: RF double-count + 3.6 dispatch
# =============================================================================


async def _seed_travel_factors(session):
    factors = [
        EmissionFactor(
            id=uuid4(),
            activity_key="flight_long_economy",
            display_name="Long-haul Flight (Economy)",
            scope=3,
            category_code="3.6",
            co2e_factor=Decimal("0.20011"),
            activity_unit="km",
            factor_unit="kg CO2e/passenger-km",
            source="DEFRA_2024",
            region="Global",
            year=2024,
            status="approved",
            notes="DEFRA 2024: Long-haul economy per passenger.km (with RF)",
        ),
        EmissionFactor(
            id=uuid4(),
            activity_key="flight_long_business",
            display_name="Long-haul Flight (Business)",
            scope=3,
            category_code="3.6",
            co2e_factor=Decimal("0.58028"),
            activity_unit="km",
            factor_unit="kg CO2e/passenger-km",
            source="DEFRA_2024",
            region="Global",
            year=2024,
            status="approved",
            notes="DEFRA 2024: Long-haul business per passenger.km (with RF)",
        ),
        # RF-exclusive flight factor (no "with RF" note) — RF must be applied.
        EmissionFactor(
            id=uuid4(),
            activity_key="flight_short_economy",
            display_name="Short-haul Flight (Economy)",
            scope=3,
            category_code="3.6",
            co2e_factor=Decimal("0.10000"),
            activity_unit="km",
            factor_unit="kg CO2e/passenger-km",
            source="TEST",
            region="Global",
            year=2024,
            status="approved",
        ),
        EmissionFactor(
            id=uuid4(),
            activity_key="hotel_night",
            display_name="Hotel Stay",
            scope=3,
            category_code="3.6",
            co2e_factor=Decimal("14.6"),
            activity_unit="nights",
            factor_unit="kg CO2e/night",
            source="DEFRA_2024",
            region="Global",
            year=2024,
            status="approved",
        ),
        EmissionFactor(
            id=uuid4(),
            activity_key="hotel_night",
            display_name="Hotel Stay (Israel)",
            scope=3,
            category_code="3.6",
            co2e_factor=Decimal("21.7"),
            activity_unit="nights",
            factor_unit="kg CO2e/night",
            source="IEC",
            region="IL",
            year=2024,
            status="approved",
        ),
    ]
    for f in factors:
        session.add(f)
    await session.commit()


async def test_flight_rf_inclusive_factor_not_doubled(test_session):
    await _seed_travel_factors(test_session)
    pipeline = CalculationPipeline(test_session)
    result = await pipeline.calculate(
        ActivityInput(
            activity_key="flight_long_economy",
            quantity=Decimal("1000"),
            unit="km",
            scope=3,
            category_code="3.6",
            region="Global",
            year=2024,
        )
    )
    # RF-inclusive factor: exactly km × factor, NO extra ×1.9.
    assert float(result.co2e_kg) == pytest.approx(1000 * 0.20011, rel=1e-6)


async def test_flight_rf_exclusive_factor_gets_rf(test_session):
    await _seed_travel_factors(test_session)
    pipeline = CalculationPipeline(test_session)
    result = await pipeline.calculate(
        ActivityInput(
            activity_key="flight_short_economy",
            quantity=Decimal("1000"),
            unit="km",
            scope=3,
            category_code="3.6",
            region="Global",
            year=2024,
        )
    )
    assert float(result.co2e_kg) == pytest.approx(1000 * 0.1 * 1.9, rel=1e-6)


async def test_hotel_not_routed_through_flight_calculator(test_session):
    await _seed_travel_factors(test_session)
    pipeline = CalculationPipeline(test_session)
    result = await pipeline.calculate(
        ActivityInput(
            activity_key="hotel_night",
            quantity=Decimal("10"),
            unit="nights",
            scope=3,
            category_code="3.6",
            region="Global",
            year=2024,
        )
    )
    # 10 nights × 14.6 — and no aviation RF ×1.9 on a hotel.
    assert float(result.co2e_kg) == pytest.approx(10 * 14.6, rel=1e-6)


async def test_hotel_country_factor_selected_by_region(test_session):
    await _seed_travel_factors(test_session)
    pipeline = CalculationPipeline(test_session)
    result = await pipeline.calculate(
        ActivityInput(
            activity_key="hotel_night",
            quantity=Decimal("3"),
            unit="nights",
            scope=3,
            category_code="3.6",
            region="IL",
            year=2024,
        )
    )
    assert float(result.co2e_kg) == pytest.approx(3 * 21.7, rel=1e-6)


# =============================================================================
# Orchestrator integration: derive → stage → answer → commit
# =============================================================================

_CSV = (
    b"Activity,Quantity\n"
    b"Flight TLV-JFK 2 passengers,2\n"
    b"Hotel stay Israel 3 nights,3\n"
)


@pytest.fixture
async def ingestion(test_session, test_org, test_user, test_period):
    s = IngestionSession(
        organization_id=test_org.id,
        created_by=test_user.id,
        reporting_period_id=test_period.id,
        filename="travel.csv",
        file_size_bytes=len(_CSV),
    )
    test_session.add(s)
    await test_session.commit()
    await test_session.refresh(s)
    return s


def _fake_mapper(rows):
    def _map(*args, **kwargs):
        return rows

    return _map


def _fake_extract(entities_by_id):
    def _extract(items, client=None, context=None):
        return entities_by_id

    return _extract


async def test_derivation_end_to_end(
    test_session, test_org, test_user, test_period, ingestion, monkeypatch
):
    await _seed_travel_factors(test_session)

    mapped = [
        MappedRow(
            0,
            "flight_long_economy",
            3,
            "3.6",
            2,
            "km",
            "Flight TLV-JFK 2 passengers",
            0.9,
            None,
            {"Activity": "Flight TLV-JFK 2 passengers", "Quantity": 2},
            True,  # unit defaulted from the factor — the demo trap
        ),
        MappedRow(
            1,
            "hotel_night",
            3,
            "3.6",
            3,
            "nights",
            "Hotel stay Israel 3 nights",
            0.9,
            None,
            {"Activity": "Hotel stay Israel 3 nights", "Quantity": 3},
            True,
        ),
    ]
    monkeypatch.setattr(orchestrator, "map_table_fast", _fake_mapper(mapped))
    monkeypatch.setattr(orchestrator, "map_table", _fake_mapper(mapped))
    monkeypatch.setattr(
        derivation,
        "extract_entities",
        _fake_extract(
            {
                0: TravelEntities(
                    kind="flight",
                    origin_text="TLV",
                    destination_text="JFK",
                    direction="unspecified",
                    bare_number_role="travelers",
                ),
                1: TravelEntities(
                    kind="hotel",
                    nights=3,
                    stay_location_text="Israel",
                    bare_number_role="nights",
                ),
            }
        ),
    )

    await orchestrator.run_analysis(
        test_session, ingestion, _CSV, "travel.csv", region="Global", year=2024
    )

    rows = (
        (
            await test_session.execute(
                select(StagedRow)
                .where(StagedRow.session_id == ingestion.id)
                .order_by(StagedRow.row_index)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2
    flight, hotel = rows

    gcd = calculate_flight_distance("TLV", "JFK")
    expected_flight_km = round(gcd * GCD_UPLIFT * 2 * 2, 1)  # RT × 2 travelers
    assert flight.quantity == pytest.approx(expected_flight_km, rel=1e-4)
    assert flight.unit == "km"
    assert flight.measurement_tier == "estimated"
    assert flight.pcaf_data_quality >= 4
    assert flight.provenance["derivation"]["engine"] == "flight"
    assert any("round trip" in r.lower() for r in flight.reasons)

    assert hotel.quantity == 3.0
    assert hotel.region == "IL"
    assert hotel.measurement_tier == "estimated"
    # Review-time grounding already uses the stay country, so the grid shows
    # the factor that will actually be committed.
    assert hotel.provenance["factor_region"] == "IL"

    questions = (
        (
            await test_session.execute(
                select(ClarificationQuestion).where(
                    ClarificationQuestion.session_id == ingestion.id
                )
            )
        )
        .scalars()
        .all()
    )
    by_text = {q.question: q for q in questions}
    rt_q = next(q for q in questions if "ROUND TRIP" in q.question)
    class_q = next(q for q in questions if "cabin" in q.question.lower())
    assert str(flight.id) in rt_q.applies_to_row_ids
    assert by_text  # sanity

    # Answer: flights were actually one-way → quantity halves, still ESTIMATED.
    await orchestrator.apply_answers(
        test_session, ingestion, {rt_q.id: "one_way"}, region="Global", year=2024
    )
    await test_session.refresh(flight)
    assert flight.quantity == pytest.approx(expected_flight_km / 2, rel=1e-4)
    assert flight.measurement_tier == "estimated"
    assert flight.provenance["derivation"]["round_trip"] is False

    # Answer: cabin class is business → key swaps, quantity untouched.
    await orchestrator.apply_answers(
        test_session,
        ingestion,
        {class_q.id: "flight_long_business"},
        region="Global",
        year=2024,
    )
    await test_session.refresh(flight)
    assert flight.activity_key == "flight_long_business"
    assert flight.quantity == pytest.approx(expected_flight_km / 2, rel=1e-4)

    # Commit: emissions computed with the derived quantities; the hotel uses
    # the STAY country's factor; assumptions land on the activity.
    for r in (flight, hotel):
        r.status = RowStatus.APPROVED
    await test_session.commit()
    await orchestrator.commit_session(test_session, ingestion)

    activities = (
        (
            await test_session.execute(
                select(Activity).where(Activity.organization_id == test_org.id)
            )
        )
        .scalars()
        .all()
    )
    by_key = {a.activity_key: a for a in activities}
    assert set(by_key) == {"flight_long_business", "hotel_night"}
    assert by_key["flight_long_business"].data_quality_justification
    assert "gazetteer" in by_key["flight_long_business"].data_quality_justification

    emissions = (await test_session.execute(select(Emission))).scalars().all()
    co2e_by_activity = {e.activity_id: float(e.co2e_kg) for e in emissions}
    assert co2e_by_activity[by_key["flight_long_business"].id] == pytest.approx(
        (expected_flight_km / 2) * 0.58028, rel=1e-4
    )
    assert co2e_by_activity[by_key["hotel_night"].id] == pytest.approx(
        3 * 21.7, rel=1e-4  # Israel factor, not the 14.6 global average
    )
