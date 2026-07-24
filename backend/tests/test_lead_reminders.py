"""
Uncontacted-lead reminder sweep + founder signature on lead emails.

The sweep must remind the founder exactly once per overdue lead, retry on a
failed send, and stay silent for fresh/contacted/stamped leads. The founder
signature (name, title, logo, climatrix.co) must ride every prospect-facing
lead email.
"""

from datetime import datetime, timedelta

import pytest

from app.config import settings
from app.models.crm import Lead
from app.services.email import email_service
from app.services.lead_reminders import send_due_lead_reminders


def _lead(email: str, age_hours: float, status: str = "new", **kw) -> Lead:
    return Lead(
        email=email,
        source="website_demo",
        status=status,
        created_at=datetime.utcnow() - timedelta(hours=age_hours),
        **kw,
    )


@pytest.mark.asyncio
async def test_overdue_lead_triggers_one_digest_and_stamps(test_session, monkeypatch):
    test_session.add(_lead("old@x.com", 72, name="Old Lead", organization_name="OldCo"))
    test_session.add(_lead("older@x.com", 100))
    await test_session.commit()

    digests = []
    monkeypatch.setattr(
        email_service,
        "send_lead_reminder_email",
        lambda leads: digests.append(leads) or True,
    )

    assert await send_due_lead_reminders(test_session) == 2
    assert len(digests) == 1  # one digest, not one email per lead
    assert {lead["email"] for lead in digests[0]} == {"old@x.com", "older@x.com"}

    for lead in (await test_session.execute(Lead.__table__.select())).fetchall():
        assert lead.reminder_sent_at is not None
        assert f"{settings.lead_reminder_hours}h-uncontacted reminder" in lead.notes


@pytest.mark.asyncio
async def test_fresh_contacted_and_stamped_leads_are_skipped(test_session, monkeypatch):
    test_session.add(_lead("fresh@x.com", 1))
    test_session.add(_lead("contacted@x.com", 90, status="contacted"))
    stamped = _lead("stamped@x.com", 90)
    stamped.reminder_sent_at = datetime.utcnow()
    test_session.add(stamped)
    await test_session.commit()

    digests = []
    monkeypatch.setattr(
        email_service,
        "send_lead_reminder_email",
        lambda leads: digests.append(leads) or True,
    )

    assert await send_due_lead_reminders(test_session) == 0
    assert digests == []


@pytest.mark.asyncio
async def test_failed_send_leaves_leads_unstamped_for_retry(test_session, monkeypatch):
    test_session.add(_lead("old@x.com", 72))
    await test_session.commit()

    monkeypatch.setattr(email_service, "send_lead_reminder_email", lambda leads: False)
    assert await send_due_lead_reminders(test_session) == 0

    row = (await test_session.execute(Lead.__table__.select())).fetchone()
    assert row.reminder_sent_at is None


@pytest.mark.asyncio
async def test_zero_hours_disables_sweep(test_session, monkeypatch):
    test_session.add(_lead("old@x.com", 72))
    await test_session.commit()

    monkeypatch.setattr(settings, "lead_reminder_hours", 0)
    called = []
    monkeypatch.setattr(
        email_service,
        "send_lead_reminder_email",
        lambda leads: called.append(1) or True,
    )

    assert await send_due_lead_reminders(test_session) == 0
    assert called == []


def test_reminder_digest_targets_founder_with_mailto(monkeypatch):
    monkeypatch.setattr(settings, "signup_notification_email", "founder@x.co")

    sent = []
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda to_email, subject, html, text: sent.append((to_email, subject, html))
        or True,
    )

    assert email_service.send_lead_reminder_email(
        [
            {
                "email": "prospect@co.com",
                "name": "Pat Prospect",
                "organization_name": "Co Ltd",
                "source": "website_demo",
                "age_hours": 60.0,
                "what_tried": None,
            }
        ]
    )
    to_email, subject, html = sent[0]
    assert to_email == "founder@x.co"
    assert "without contact" in subject
    assert "mailto:prospect@co.com" in html


def test_lead_ack_carries_founder_signature(monkeypatch):
    sent = []
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda to_email, subject, html, text: sent.append((html, text)) or True,
    )

    assert email_service.send_lead_ack_email("new@co.com", "New Person")
    html, text = sent[0]
    assert email_service.LOGO_URL in html
    assert "Founder &amp; CEO" in html or "Founder & CEO" in html
    assert "https://climatrix.co" in html
    assert "Avi Luvchik" in text


def test_lead_ack_booking_button_follows_setting(monkeypatch):
    sent = []
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda to_email, subject, html, text: sent.append((html, text)) or True,
    )

    email_service.send_lead_ack_email("a@co.com", None)
    assert "Pick a demo time" not in sent[0][0]  # unset by default

    monkeypatch.setattr(settings, "demo_booking_url", "https://cal.example/avi")
    email_service.send_lead_ack_email("b@co.com", None)
    html, text = sent[1]
    assert "Pick a demo time" in html
    assert "https://cal.example/avi" in html
    assert "https://cal.example/avi" in text
