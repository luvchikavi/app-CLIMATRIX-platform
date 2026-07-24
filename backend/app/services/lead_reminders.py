"""
Uncontacted-lead reminder sweep.

A lead who asked for a demo and then sits in "new" is a lost sale in slow
motion. This background loop checks periodically and sends the founder ONE
digest email per sweep listing every lead that has waited longer than
settings.lead_reminder_hours — then stamps each lead so it is never nagged
about twice. Runs inline in the web process (prod has no worker).
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlmodel import select

from app.config import settings
from app.models.crm import Lead
from app.services.email import email_service

logger = logging.getLogger(__name__)

# Give boot/migrations time to settle before the first sweep.
_FIRST_SWEEP_DELAY_SECONDS = 120


async def send_due_lead_reminders(session) -> int:
    """One sweep: digest-email the founder about overdue 'new' leads.

    Returns the number of leads included (0 if nothing due or disabled).
    """
    if settings.lead_reminder_hours <= 0 or not settings.signup_notification_email:
        return 0

    now = datetime.utcnow()
    cutoff = now - timedelta(hours=settings.lead_reminder_hours)

    result = await session.execute(
        select(Lead).where(
            Lead.status == "new",
            Lead.reminder_sent_at.is_(None),
            Lead.created_at <= cutoff,
        )
    )
    leads = result.scalars().all()
    if not leads:
        return 0

    payload = [
        {
            "email": lead.email,
            "name": lead.name,
            "organization_name": lead.organization_name,
            "source": lead.source,
            "age_hours": (now - lead.created_at).total_seconds() / 3600,
            "what_tried": lead.what_tried,
        }
        for lead in leads
    ]

    if not email_service.send_lead_reminder_email(payload):
        # Sending failed — leave leads unstamped so the next sweep retries.
        return 0

    stamp = now.strftime("%Y-%m-%d")
    note = f"[{stamp}] {settings.lead_reminder_hours}h-uncontacted reminder sent"
    for lead in leads:
        lead.reminder_sent_at = now
        lead.notes = f"{lead.notes}\n{note}" if lead.notes else note
        lead.updated_at = now
    await session.commit()

    logger.info("Lead reminder sent for %d uncontacted lead(s)", len(leads))
    return len(leads)


async def lead_reminder_loop() -> None:
    """Forever-loop started from the app lifespan; must never crash the app."""
    await asyncio.sleep(_FIRST_SWEEP_DELAY_SECONDS)
    while True:
        try:
            from app.database import async_session_maker

            async with async_session_maker() as session:
                await send_due_lead_reminders(session)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Lead reminder sweep failed; will retry next cycle")
        await asyncio.sleep(max(1, settings.lead_reminder_check_minutes) * 60)
