"""
Founder signup-notification email: every new registration pings the
founder inbox (settings.signup_notification_email), alongside the welcome
email to the user — and neither may ever break the signup itself.
"""

import pytest
from httpx import AsyncClient

from app.services.email import email_service

_PAYLOAD = {
    "email": "fresh@company.com",
    "password": "newpassword123",
    "full_name": "Fresh User",
    "organization_name": "Fresh Co",
    "country_code": "US",
}


@pytest.mark.asyncio
async def test_register_notifies_founder(client: AsyncClient, monkeypatch):
    notified = []
    monkeypatch.setattr(
        email_service,
        "send_signup_notification_email",
        lambda new_user_email, user_name, org_name: notified.append(
            (new_user_email, user_name, org_name)
        )
        or True,
    )

    response = await client.post("/api/auth/register", json=_PAYLOAD)
    assert response.status_code == 200
    assert notified == [("fresh@company.com", "Fresh User", "Fresh Co")]


@pytest.mark.asyncio
async def test_notification_failure_never_breaks_signup(
    client: AsyncClient, monkeypatch
):
    def boom(new_user_email, user_name, org_name):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(email_service, "send_signup_notification_email", boom)

    response = await client.post("/api/auth/register", json=_PAYLOAD)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_notification_disabled_when_address_empty(monkeypatch):
    """Empty signup_notification_email disables the ping without erroring."""
    from app.config import settings

    monkeypatch.setattr(settings, "signup_notification_email", "")

    sent = []
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda *args, **kwargs: sent.append(args) or True,
    )

    assert email_service.send_signup_notification_email(
        new_user_email="x@y.com", user_name="X", org_name="Y"
    )
    assert sent == []


def test_notification_targets_configured_address(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "signup_notification_email", "founder@x.co")

    sent = []
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda to_email, subject, html, text: sent.append((to_email, subject)) or True,
    )

    assert email_service.send_signup_notification_email(
        new_user_email="new@org.com", user_name="New Person", org_name="Org Inc"
    )
    assert sent == [("founder@x.co", "New CLIMATRIX signup: Org Inc")]
