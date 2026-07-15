"""
Tests for the lightweight lead-management (CRM) module.

Covers public lead capture (no auth), admin listing, and status updates.
"""

import pytest


@pytest.mark.asyncio
async def test_public_capture_creates_lead(client):
    """Anonymous users can capture a lead without auth."""
    resp = await client.post(
        "/api/leads",
        json={
            "email": "jane@example.com",
            "name": "Jane Doe",
            "organization_name": "Acme Co",
            "source": "website_tryit",
            "what_tried": "emissions.xlsx",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == "jane@example.com"
    assert data["name"] == "Jane Doe"
    assert data["source"] == "website_tryit"
    assert data["status"] == "new"
    assert data["what_tried"] == "emissions.xlsx"


@pytest.mark.asyncio
async def test_public_capture_upserts_by_email(client):
    """Capturing the same email twice updates rather than duplicating."""
    first = await client.post(
        "/api/leads",
        json={"email": "dup@example.com", "source": "conference"},
    )
    assert first.status_code == 200
    lead_id = first.json()["id"]

    second = await client.post(
        "/api/leads",
        json={
            "email": "dup@example.com",
            "name": "Now Named",
            "source": "forum",
        },
    )
    assert second.status_code == 200
    body = second.json()
    # Same underlying record, updated details.
    assert body["id"] == lead_id
    assert body["name"] == "Now Named"
    assert body["source"] == "forum"


@pytest.mark.asyncio
async def test_public_capture_rejects_invalid_source(client):
    resp = await client.post(
        "/api/leads",
        json={"email": "bad@example.com", "source": "not_a_source"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_leads_requires_auth(client):
    resp = await client.get("/api/leads")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_and_filters(client, admin_headers):
    """Admin can list leads newest-first with status/source filters."""
    await client.post(
        "/api/leads",
        json={"email": "a@example.com", "source": "conference"},
    )
    await client.post(
        "/api/leads",
        json={"email": "b@example.com", "source": "forum"},
    )

    # List all
    resp = await client.get("/api/leads", headers=admin_headers)
    assert resp.status_code == 200
    leads = resp.json()
    assert len(leads) >= 2
    # Newest first: b was created after a
    emails = [lead["email"] for lead in leads]
    assert emails.index("b@example.com") < emails.index("a@example.com")

    # Filter by source
    resp = await client.get("/api/leads?source=forum", headers=admin_headers)
    assert resp.status_code == 200
    forum_leads = resp.json()
    assert all(lead["source"] == "forum" for lead in forum_leads)
    assert any(lead["email"] == "b@example.com" for lead in forum_leads)


@pytest.mark.asyncio
async def test_admin_update_status_and_notes(client, admin_headers):
    """Admin can update a lead's status and notes."""
    created = await client.post(
        "/api/leads",
        json={"email": "follow@example.com", "source": "signup"},
    )
    lead_id = created.json()["id"]

    resp = await client.patch(
        f"/api/leads/{lead_id}",
        headers=admin_headers,
        json={"status": "contacted", "notes": "Emailed on Monday"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "contacted"
    assert body["notes"] == "Emailed on Monday"
    assert body["updated_at"] is not None

    # Status filter now reflects the update.
    listing = await client.get("/api/leads?status=contacted", headers=admin_headers)
    assert any(lead["id"] == lead_id for lead in listing.json())


@pytest.mark.asyncio
async def test_admin_update_rejects_invalid_status(client, admin_headers):
    created = await client.post(
        "/api/leads",
        json={"email": "invalid-status@example.com", "source": "manual"},
    )
    lead_id = created.json()["id"]

    resp = await client.patch(
        f"/api/leads/{lead_id}",
        headers=admin_headers,
        json={"status": "nonsense"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_leads_forbidden_for_org_admin(client, auth_headers):
    """The lead book is company-internal: org admins get 403, not the pipeline."""
    resp = await client.get("/api/leads", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_lead_forbidden_for_org_admin(client, auth_headers, admin_headers):
    created = await client.post(
        "/api/leads",
        json={"email": "gated@example.com", "source": "manual"},
    )
    lead_id = created.json()["id"]

    resp = await client.patch(
        f"/api/leads/{lead_id}",
        headers=auth_headers,
        json={"status": "contacted"},
    )
    assert resp.status_code == 403

    # Super admin still can.
    resp = await client.patch(
        f"/api/leads/{lead_id}",
        headers=admin_headers,
        json={"status": "contacted"},
    )
    assert resp.status_code == 200
