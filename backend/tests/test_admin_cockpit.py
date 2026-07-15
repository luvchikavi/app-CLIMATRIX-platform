"""Tests for the super-admin cockpit aggregate endpoint."""

import pytest


@pytest.mark.asyncio
async def test_cockpit_requires_super_admin(client, auth_headers):
    """Org admins are not company admins — 403."""
    resp = await client.get("/api/admin/cockpit", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cockpit_requires_auth(client):
    resp = await client.get("/api/admin/cockpit")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_cockpit_shape_and_counts(client, admin_headers, test_user):
    """The cockpit returns every panel's data in one round-trip."""
    # Seed one lead so the pipeline has something to count.
    await client.post(
        "/api/leads",
        json={"email": "cockpit-lead@example.com", "source": "conference"},
    )

    resp = await client.get("/api/admin/cockpit", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # The test org + its users exist (test_user + test_admin fixtures).
    assert body["organizations_total"] >= 1
    assert body["users_total"] >= 2

    # 14 buckets, today included, each day ISO-dated.
    assert len(body["signups_14d"]) == 14
    assert all("day" in d and "signups" in d for d in body["signups_14d"])
    # The fixture users were created just now — the window counts them
    # (bucketed by UTC date, which near midnight may be yesterday's bucket).
    assert sum(d["signups"] for d in body["signups_14d"]) >= 2

    # Pipeline always enumerates the five stages, in order.
    stages = [s["status"] for s in body["lead_pipeline"]]
    assert stages == ["new", "contacted", "trial", "customer", "lost"]
    assert body["leads_total"] >= 1
    assert body["leads_open"] >= 1

    # Recent panels are lists with the seeded entries visible.
    assert any(
        lead["email"] == "cockpit-lead@example.com" for lead in body["recent_leads"]
    )
    assert len(body["recent_signups"]) >= 1

    # Finance block present (no paid orgs in fixtures => zero MRR).
    assert body["mrr_usd"] >= 0
    assert isinstance(body["plans"], list)
