"""
Tests for the lightweight lead-management (CRM) module.

Covers public lead capture (no auth), admin listing, and status updates.
"""

import pytest


async def _lead_by_email(client, admin_headers, email: str) -> dict:
    listing = await client.get("/api/leads", headers=admin_headers)
    assert listing.status_code == 200
    return next(lead for lead in listing.json() if lead["email"] == email)


@pytest.mark.asyncio
async def test_public_capture_creates_lead(client, admin_headers):
    """Anonymous users can capture a lead — and get NOTHING back but an ack:
    reflecting the stored lead would leak internal notes/pipeline status."""
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
    assert resp.json() == {"ok": True}

    stored = await _lead_by_email(client, admin_headers, "jane@example.com")
    assert stored["name"] == "Jane Doe"
    assert stored["source"] == "website_tryit"
    assert stored["status"] == "new"
    assert stored["what_tried"] == "emissions.xlsx"


@pytest.mark.asyncio
async def test_public_capture_upserts_by_email(client, admin_headers):
    """Capturing the same email twice fills gaps rather than duplicating —
    and an anonymous POST can never OVERWRITE what the pipeline knows."""
    first = await client.post(
        "/api/leads",
        json={"email": "dup@example.com", "source": "conference"},
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/leads",
        json={
            "email": "dup@example.com",
            "name": "Now Named",
            "source": "forum",
        },
    )
    assert second.status_code == 200

    listing = await client.get("/api/leads", headers=admin_headers)
    dups = [lead for lead in listing.json() if lead["email"] == "dup@example.com"]
    assert len(dups) == 1
    assert dups[0]["name"] == "Now Named"  # empty field got filled
    assert dups[0]["source"] == "conference"  # existing value NOT overwritten


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
    await client.post(
        "/api/leads",
        json={"email": "follow@example.com", "source": "signup"},
    )
    lead_id = (await _lead_by_email(client, admin_headers, "follow@example.com"))["id"]

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
    await client.post(
        "/api/leads",
        json={"email": "invalid-status@example.com", "source": "manual"},
    )
    lead_id = (
        await _lead_by_email(client, admin_headers, "invalid-status@example.com")
    )["id"]

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
    await client.post(
        "/api/leads",
        json={"email": "gated@example.com", "source": "manual"},
    )
    lead_id = (await _lead_by_email(client, admin_headers, "gated@example.com"))["id"]

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


@pytest.mark.asyncio
async def test_new_website_lead_gets_auto_ack(client, monkeypatch):
    """A first-time website-form lead triggers the instant acknowledgment."""
    from app.services.email import email_service

    sent = []
    monkeypatch.setattr(
        email_service,
        "send_lead_ack_email",
        lambda to_email, lead_name: sent.append((to_email, lead_name)) or True,
    )

    resp = await client.post(
        "/api/leads",
        json={
            "email": "ack@example.com",
            "name": "Ack Person",
            "source": "website_demo",
        },
    )
    assert resp.status_code == 200
    assert sent == [("ack@example.com", "Ack Person")]


@pytest.mark.asyncio
async def test_repeat_lead_gets_no_auto_ack(client, monkeypatch):
    """Re-submitting an existing lead must NOT re-send the acknowledgment —
    otherwise the public endpoint becomes an email cannon."""
    from app.services.email import email_service

    sent = []
    monkeypatch.setattr(
        email_service,
        "send_lead_ack_email",
        lambda to_email, lead_name: sent.append(to_email) or True,
    )

    for _ in range(2):
        resp = await client.post(
            "/api/leads",
            json={"email": "once@example.com", "source": "website_trial"},
        )
        assert resp.status_code == 200

    assert sent == ["once@example.com"]


@pytest.mark.asyncio
async def test_founder_entered_sources_get_no_auto_ack(client, monkeypatch):
    """conference/manual/signup leads are not live form submissions —
    no automated 'we saw your message' for them."""
    from app.services.email import email_service

    sent = []
    monkeypatch.setattr(
        email_service,
        "send_lead_ack_email",
        lambda to_email, lead_name: sent.append(to_email) or True,
    )

    for i, source in enumerate(["conference", "manual", "signup"]):
        resp = await client.post(
            "/api/leads",
            json={"email": f"noack{i}@example.com", "source": source},
        )
        assert resp.status_code == 200

    assert sent == []


@pytest.mark.asyncio
async def test_auto_ack_failure_never_breaks_capture(client, monkeypatch):
    """Email backend blowing up must not lose the lead."""
    from app.services.email import email_service

    def boom(to_email, lead_name):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(email_service, "send_lead_ack_email", boom)

    resp = await client.post(
        "/api/leads",
        json={"email": "boom@example.com", "source": "website_tryit"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
