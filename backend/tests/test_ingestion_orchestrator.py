"""End-to-end orchestrator test: upload → stage → answer → commit.

The single LLM mapping call is monkeypatched with deterministic MappedRows so the
whole pipeline (grounding, rules, scoring, staging, question flow, and the real
CalculationPipeline commit) is exercised without an API key.
"""

import pytest
from sqlalchemy import select

from app.models.emission import Activity, Emission
from app.models.ingestion import (
    IngestionSession,
    IngestionStatus,
    RowStatus,
    StagedRow,
    ClarificationQuestion,
)
from app.services.ingestion import orchestrator
from app.services.ingestion.mapper import MappedRow

_CSV = (
    b"Activity,Quantity,Unit\n"
    b"Office electricity,45600,kWh\n"
    b"Natural gas heating,1000,m3\n"
    b"Something unusual,5,widgets\n"
)


def _fake_map(rows):
    def _map_table(table, catalog, max_rows=None, client=None):
        return rows

    return _map_table


@pytest.fixture
async def ingestion(test_session, test_org, test_user, test_period):
    s = IngestionSession(
        organization_id=test_org.id,
        created_by=test_user.id,
        reporting_period_id=test_period.id,
        filename="footprint.csv",
        file_size_bytes=len(_CSV),
    )
    test_session.add(s)
    await test_session.commit()
    await test_session.refresh(s)
    return s


async def test_full_ingestion_flow(
    test_session,
    test_org,
    test_user,
    test_period,
    seed_emission_factors,
    ingestion,
    monkeypatch,
):
    mapped = [
        # clean, grounds exactly -> READY
        MappedRow(
            0,
            "electricity_kwh",
            2,
            "2",
            45600,
            "kWh",
            "Office electricity",
            0.95,
            None,
            {},
        ),
        # unit mismatch: factor expects kWh, client gave m3 -> question
        MappedRow(
            1,
            "natural_gas_kwh",
            1,
            "1.1",
            1000,
            "m3",
            "Natural gas heating",
            0.9,
            "Gas is in m3 but the factor expects kWh — which did you mean?",
            {},
        ),
        # no confident key -> question
        MappedRow(
            2,
            None,
            None,
            None,
            5,
            "widgets",
            "Something unusual",
            0.3,
            "We couldn't match this — which activity is it?",
            {},
        ),
    ]
    monkeypatch.setattr(orchestrator, "map_table_fast", _fake_map(mapped))
    monkeypatch.setattr(orchestrator, "map_table", _fake_map(mapped))

    # 1) ANALYZE
    await orchestrator.run_analysis(test_session, ingestion, _CSV, "footprint.csv")
    await test_session.commit()

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
    assert len(rows) == 3
    assert rows[0].activity_key == "electricity_kwh"
    assert rows[0].status == RowStatus.READY
    assert rows[0].band == "green"
    assert rows[1].status == RowStatus.NEEDS_QUESTION  # unit mismatch
    assert rows[2].status == RowStatus.NEEDS_QUESTION  # no key

    qs = (
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
    assert len(qs) == 2
    assert ingestion.status == IngestionStatus.NEEDS_ANSWERS
    assert ingestion.open_question_count == 2

    # 2) ANSWER — fix the gas unit, and classify the unknown row as petrol
    answers = {}
    for q in qs:
        row = await test_session.get(StagedRow, q.staged_row_id)
        if row.activity_key == "natural_gas_kwh":
            answers[q.id] = "kWh"  # field == 'unit'
        else:
            answers[q.id] = "petrol_liters"  # field == 'activity'
    await orchestrator.apply_answers(test_session, ingestion, answers)
    await test_session.commit()

    assert ingestion.open_question_count == 0
    assert ingestion.status == IngestionStatus.READY_FOR_REVIEW

    gas = (
        (
            await test_session.execute(
                select(StagedRow).where(
                    StagedRow.session_id == ingestion.id,
                    StagedRow.activity_key == "natural_gas_kwh",
                )
            )
        )
        .scalars()
        .one()
    )
    assert gas.unit == "kWh"
    assert (
        gas.status == RowStatus.NEEDS_REVIEW
    )  # answered rows go to human review, not auto-ready

    unknown = (
        (
            await test_session.execute(
                select(StagedRow).where(
                    StagedRow.session_id == ingestion.id, StagedRow.row_index == 2
                )
            )
        )
        .scalars()
        .one()
    )
    assert unknown.activity_key == "petrol_liters"
    assert unknown.scope == 1  # pulled from catalog entry, not the LLM

    # 3) COMMIT — approve the two answered rows; the electricity row is already READY
    gas.status = RowStatus.APPROVED
    unknown.status = RowStatus.APPROVED
    await test_session.commit()

    await orchestrator.commit_session(test_session, ingestion)
    await test_session.commit()

    assert ingestion.status == IngestionStatus.COMMITTED
    # electricity + gas commit cleanly; petrol still carries unit "widgets", so the
    # real pipeline rejects it at commit — the safety net that keeps junk out of the ledger.
    assert ingestion.committed_count == 2

    activities = (
        (
            await test_session.execute(
                select(Activity).where(Activity.organization_id == test_org.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(activities) == 2
    emissions = (await test_session.execute(select(Emission))).scalars().all()
    assert len(emissions) == 2
    assert all(e.co2e_kg is not None for e in emissions)
    # staged rows now point at the real activities they created
    committed_rows = (
        (
            await test_session.execute(
                select(StagedRow).where(
                    StagedRow.session_id == ingestion.id,
                    StagedRow.status == RowStatus.COMMITTED,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(committed_rows) == 2
    assert all(r.committed_activity_id is not None for r in committed_rows)
    # Provenance drift guard: the staged audit trail must describe the factor
    # that was ACTUALLY committed, not the one shown at review time.
    for r in committed_rows:
        emission = (
            (
                await test_session.execute(
                    select(Emission).where(
                        Emission.activity_id == r.committed_activity_id
                    )
                )
            )
            .scalars()
            .one()
        )
        assert r.provenance["factor_year"] == emission.factor_year
        assert r.provenance["factor_region"] == emission.factor_region
        assert r.provenance["method"] == emission.resolution_strategy
    # the bad-unit row is left un-committed with an explanatory error for the review grid
    petrol = await test_session.get(StagedRow, unknown.id)
    assert petrol.committed_activity_id is None
    assert petrol.commit_error is not None


async def test_year_threading_and_assumed_year_reason(
    test_session,
    test_org,
    test_user,
    test_period,
    seed_emission_factors,
    ingestion,
    monkeypatch,
):
    """The real reporting-period year must reach grounding; a missing year falls
    back to the CURRENT year (never a hardcoded vintage) and says so on the row."""
    from datetime import datetime as dt

    mapped = [
        MappedRow(
            0,
            "electricity_kwh",
            2,
            "2",
            45600,
            "kWh",
            "Office electricity",
            0.95,
            None,
            {},
        ),
    ]
    monkeypatch.setattr(orchestrator, "map_table_fast", _fake_map(mapped))
    monkeypatch.setattr(orchestrator, "map_table", _fake_map(mapped))

    seen_years = []
    real_ground = orchestrator.ground_row

    async def spy_ground(session, key, unit, *, region="Global", year=2024):
        seen_years.append(year)
        return await real_ground(session, key, unit, region=region, year=year)

    monkeypatch.setattr(orchestrator, "ground_row", spy_ground)

    # 1) With an explicit period year (2025) — grounding must receive it.
    await orchestrator.run_analysis(
        test_session, ingestion, _CSV, "footprint.csv", year=2025
    )
    await test_session.commit()
    assert seen_years and all(y == 2025 for y in seen_years)

    row = (
        (
            await test_session.execute(
                select(StagedRow).where(StagedRow.session_id == ingestion.id)
            )
        )
        .scalars()
        .first()
    )
    assert not any("assumed factor year" in r for r in (row.reasons or []))

    # 2) No year at all (ingest without a period) — current year + audit reason.
    seen_years.clear()
    await orchestrator.reground_row(test_session, row, region="Global", year=None)
    this_year = dt.utcnow().year
    assert seen_years == [this_year]
    assert any(f"assumed factor year {this_year}" in r for r in row.reasons)

    # 3) Re-grounding WITH a year again keeps the audit trail clean.
    await orchestrator.reground_row(test_session, row, region="Global", year=2025)
    assert not any("assumed factor year" in r for r in (row.reasons or []))


async def test_skipped_sheets_surface_in_summary(
    test_session,
    test_org,
    test_user,
    test_period,
    seed_emission_factors,
    monkeypatch,
):
    """Sheets skipped as empty/metadata must be listed in the session summary —
    nothing an upload contains may vanish silently."""
    import io

    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(["Activity", "Quantity", "Unit", "Site"])
    ws.append(["Office electricity", 45600, "kWh", "HQ"])
    ws.append(["Diesel", 720, "liters", "HQ"])
    ws.append(["Natural gas", 900, "kWh", "Plant"])
    wb.create_sheet("Instructions")  # empty — skipped, but must be reported
    buf = io.BytesIO()
    wb.save(buf)
    content = buf.getvalue()

    mapped = [
        MappedRow(
            0,
            "electricity_kwh",
            2,
            "2",
            45600,
            "kWh",
            "Office electricity",
            0.95,
            None,
            {},
        ),
    ]
    monkeypatch.setattr(orchestrator, "map_table_fast", _fake_map(mapped))
    monkeypatch.setattr(orchestrator, "map_table", _fake_map(mapped))

    s = IngestionSession(
        organization_id=test_org.id,
        created_by=test_user.id,
        reporting_period_id=test_period.id,
        filename="book.xlsx",
        file_size_bytes=len(content),
    )
    test_session.add(s)
    await test_session.commit()

    await orchestrator.run_analysis(test_session, s, content, "book.xlsx", year=2025)
    await test_session.commit()

    assert s.summary.get("skipped_sheets") == ["Instructions"]
