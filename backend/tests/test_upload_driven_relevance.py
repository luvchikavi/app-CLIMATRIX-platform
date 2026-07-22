"""Upload-driven relevance — commit-time auto-mark of the inventory map.

Covers every row of the design's rules table:

  profile unset      → auto-set relevant, provenance = upload
  profile not_sure   → auto-set relevant (upgrade only)
  profile relevant   → untouched, no update entry
  profile excluded   → NEVER flipped; conflict entry instead
  un-ticked session  → the same session's evidence never re-suggests

Plus: ledger code "2" rolls up to hub row "2.1", and the profile PUT no
longer wipes fields the caller didn't send (the un-tick path depends on it).
"""

import pytest
from sqlalchemy import select

from app.models.hub import CategoryProfile, CategoryRelevance
from app.models.ingestion import IngestionSession, RowStatus, StagedRow
from app.services.ingestion import orchestrator

pytestmark = pytest.mark.asyncio


async def _make_session_with_rows(
    test_session, test_org, test_user, test_period, rows: list[dict]
) -> IngestionSession:
    """An ingestion session with READY staged rows, ready to commit."""
    ing = IngestionSession(
        organization_id=test_org.id,
        created_by=test_user.id,
        reporting_period_id=test_period.id,
        filename="relevance_test.csv",
        file_size_bytes=100,
    )
    test_session.add(ing)
    await test_session.flush()
    for i, r in enumerate(rows):
        test_session.add(
            StagedRow(
                session_id=ing.id,
                row_index=i,
                status=RowStatus.READY.value,
                confidence=0.95,
                band="green",
                description=r.get("description", "row"),
                **{k: v for k, v in r.items() if k != "description"},
            )
        )
    await test_session.commit()
    await test_session.refresh(ing)
    return ing


async def _commit(test_session, ing) -> IngestionSession:
    await orchestrator.commit_session(test_session, ing)
    await test_session.commit()
    await test_session.refresh(ing)
    return ing


async def _profile_of(test_session, org_id, code) -> CategoryProfile | None:
    return (
        (
            await test_session.execute(
                select(CategoryProfile).where(
                    CategoryProfile.organization_id == org_id,
                    CategoryProfile.category_code == code,
                    CategoryProfile.site_id.is_(None),
                )
            )
        )
        .scalars()
        .one_or_none()
    )


_GAS_ROW = {
    "activity_key": "natural_gas_kwh",
    "scope": 1,
    "category_code": "1.1",
    "quantity": 1000.0,
    "unit": "kWh",
}
_ELEC_ROW = {
    "activity_key": "electricity_kwh",
    "scope": 2,
    "category_code": "2",  # ledger code — must roll up to hub row 2.1
    "quantity": 500.0,
    "unit": "kWh",
}


async def test_unset_profile_auto_marked_relevant_with_provenance(
    test_session, test_org, test_user, test_period, seed_emission_factors
):
    ing = await _make_session_with_rows(
        test_session, test_org, test_user, test_period, [_GAS_ROW, _GAS_ROW]
    )
    ing = await _commit(test_session, ing)

    assert ing.committed_count == 2
    profile = await _profile_of(test_session, test_org.id, "1.1")
    assert profile is not None
    assert profile.relevance == CategoryRelevance.RELEVANT.value
    prov = (profile.details or {}).get("relevance_provenance")
    assert prov["source"] == "upload"
    assert prov["session_id"] == str(ing.id)
    assert prov["filename"] == "relevance_test.csv"

    updates = ing.summary["profile_updates"]
    assert updates == [
        {
            "category_code": "1.1",
            "name": "Stationary Combustion",
            "row_count": 2,
            "previous_relevance": None,
        }
    ]
    assert ing.summary["profile_conflicts"] == []


async def test_not_sure_upgraded_and_existing_details_kept(
    test_session, test_org, test_user, test_period, seed_emission_factors
):
    test_session.add(
        CategoryProfile(
            organization_id=test_org.id,
            scope=1,
            category_code="1.1",
            relevance=CategoryRelevance.NOT_SURE.value,
            data_owner="Facilities",
            details={"scope2_method": "market"},
        )
    )
    await test_session.commit()

    ing = await _make_session_with_rows(
        test_session, test_org, test_user, test_period, [_GAS_ROW]
    )
    ing = await _commit(test_session, ing)

    profile = await _profile_of(test_session, test_org.id, "1.1")
    assert profile.relevance == CategoryRelevance.RELEVANT.value
    assert profile.data_owner == "Facilities"  # untouched
    assert profile.details["scope2_method"] == "market"  # merged, not replaced
    assert profile.details["relevance_provenance"]["source"] == "upload"
    assert ing.summary["profile_updates"][0]["previous_relevance"] == "not_sure"


async def test_already_relevant_untouched_no_update_entry(
    test_session, test_org, test_user, test_period, seed_emission_factors
):
    test_session.add(
        CategoryProfile(
            organization_id=test_org.id,
            scope=1,
            category_code="1.1",
            relevance=CategoryRelevance.RELEVANT.value,
            details={"relevance_provenance": {"source": "user"}},
        )
    )
    await test_session.commit()

    ing = await _make_session_with_rows(
        test_session, test_org, test_user, test_period, [_GAS_ROW]
    )
    ing = await _commit(test_session, ing)

    profile = await _profile_of(test_session, test_org.id, "1.1")
    # The user's own declaration is not restamped as upload-derived.
    assert profile.details["relevance_provenance"]["source"] == "user"
    assert ing.summary["profile_updates"] == []
    assert ing.summary["profile_conflicts"] == []


async def test_excluded_category_never_flipped_conflict_raised(
    test_session, test_org, test_user, test_period, seed_emission_factors
):
    test_session.add(
        CategoryProfile(
            organization_id=test_org.id,
            scope=1,
            category_code="1.1",
            relevance=CategoryRelevance.NOT_RELEVANT.value,
            exclusion_reason="No on-site combustion",
        )
    )
    await test_session.commit()

    ing = await _make_session_with_rows(
        test_session, test_org, test_user, test_period, [_GAS_ROW, _GAS_ROW, _GAS_ROW]
    )
    ing = await _commit(test_session, ing)

    # Rows commit anyway (warn, never block) …
    assert ing.committed_count == 3
    # … but the documented exclusion stands.
    profile = await _profile_of(test_session, test_org.id, "1.1")
    assert profile.relevance == CategoryRelevance.NOT_RELEVANT.value
    assert profile.exclusion_reason == "No on-site combustion"
    assert ing.summary["profile_updates"] == []
    assert ing.summary["profile_conflicts"] == [
        {
            "category_code": "1.1",
            "name": "Stationary Combustion",
            "row_count": 3,
            "exclusion_reason": "No on-site combustion",
        }
    ]


async def test_dismissed_session_not_resuggested(
    test_session, test_org, test_user, test_period, seed_emission_factors
):
    ing = await _make_session_with_rows(
        test_session, test_org, test_user, test_period, [_GAS_ROW]
    )
    # Simulate the un-tick: back to not_sure, dismissal recorded against
    # this session — as the frontend writes it through PUT /hub/profile.
    test_session.add(
        CategoryProfile(
            organization_id=test_org.id,
            scope=1,
            category_code="1.1",
            relevance=CategoryRelevance.NOT_SURE.value,
            details={"relevance_dismissed_sessions": [str(ing.id)]},
        )
    )
    await test_session.commit()

    ing = await _commit(test_session, ing)

    profile = await _profile_of(test_session, test_org.id, "1.1")
    assert profile.relevance == CategoryRelevance.NOT_SURE.value
    assert ing.summary["profile_updates"] == []


async def test_ledger_code_rolls_up_to_hub_row(
    test_session, test_org, test_user, test_period, seed_emission_factors
):
    ing = await _make_session_with_rows(
        test_session, test_org, test_user, test_period, [_ELEC_ROW]
    )
    ing = await _commit(test_session, ing)

    # Ledger code "2" lands on the hub's aggregate row 2.1 (electricity).
    profile = await _profile_of(test_session, test_org.id, "2.1")
    assert profile is not None
    assert profile.relevance == CategoryRelevance.RELEVANT.value
    assert ing.summary["profile_updates"][0]["category_code"] == "2.1"


async def test_profile_put_preserves_unsent_fields_and_merges_details(
    client, auth_headers, test_org, test_session
):
    """The matrix's relevance-only save must not wipe drawer answers or
    upload provenance — the un-tick path depends on this merge behavior."""
    full = {
        "entries": [
            {
                "category_code": "3.6",
                "relevance": "relevant",
                "data_owner": "Travel desk",
                "expected_form": "invoices",
                "details": {"relevance_provenance": {"source": "upload"}},
            }
        ]
    }
    resp = await client.put("/api/hub/profile", json=full, headers=auth_headers)
    assert resp.status_code == 200

    # Relevance-only save (exactly what the matrix buttons send).
    partial = {"entries": [{"category_code": "3.6", "relevance": "not_sure"}]}
    resp = await client.put("/api/hub/profile", json=partial, headers=auth_headers)
    assert resp.status_code == 200
    saved = resp.json()[0]
    assert saved["relevance"] == "not_sure"
    assert saved["data_owner"] == "Travel desk"
    assert saved["expected_form"] == "invoices"
    assert saved["details"]["relevance_provenance"] == {"source": "upload"}

    # A details write merges into the bag instead of replacing it.
    merge = {
        "entries": [
            {
                "category_code": "3.6",
                "relevance": "not_sure",
                "details": {"relevance_dismissed_sessions": ["abc"]},
            }
        ]
    }
    resp = await client.put("/api/hub/profile", json=merge, headers=auth_headers)
    assert resp.status_code == 200
    details = resp.json()[0]["details"]
    assert details["relevance_dismissed_sessions"] == ["abc"]
    assert details["relevance_provenance"] == {"source": "upload"}
