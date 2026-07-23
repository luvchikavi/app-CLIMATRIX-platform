"""
Lead-management (lightweight CRM) API endpoints.

- Public capture endpoint for people who try the app / leave details at a
  conference / come from forums (no auth, rate-limited).
- Admin endpoints to list and update leads for follow-up.
"""

from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.admin import require_super_admin
from app.config import settings
from app.database import get_session
from app.rate_limit import limiter
from app.models.core import User
from app.models.crm import Lead

router = APIRouter()

# Allowed enum-like values (kept as plain strings on the model for flexibility).
VALID_SOURCES = {
    "website_tryit",
    "website_trial",
    "website_demo",
    "conference",
    "signup",
    "forum",
    "manual",
}
VALID_STATUSES = {"new", "contacted", "trial", "customer", "lost"}

# Sources that came in through a live website form and deserve an instant
# auto-acknowledgment email. "signup" already triggers the welcome email;
# "conference"/"manual" are entered by the founder after the fact.
AUTO_ACK_SOURCES = {"website_tryit", "website_trial", "website_demo", "forum"}


# ============================================================================
# Schemas
# ============================================================================


class LeadCapture(BaseModel):
    """Public lead-capture payload."""

    email: EmailStr
    name: Optional[str] = None
    organization_name: Optional[str] = None
    source: str
    what_tried: Optional[str] = None


class LeadUpdate(BaseModel):
    """Admin update payload for status / notes."""

    status: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Lead representation returned to clients."""

    id: str
    name: Optional[str]
    email: str
    organization_name: Optional[str]
    source: str
    status: str
    notes: Optional[str]
    what_tried: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_lead(cls, lead: Lead) -> "LeadResponse":
        return cls(
            id=str(lead.id),
            name=lead.name,
            email=lead.email,
            organization_name=lead.organization_name,
            source=lead.source,
            status=lead.status,
            notes=lead.notes,
            what_tried=lead.what_tried,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/leads")
@limiter.limit(settings.rate_limit_default)
async def capture_lead(
    request: Request,
    payload: LeadCapture,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
):
    """
    PUBLIC lead capture (no auth).

    Upserts by email: if a lead with the same email already exists it is
    updated with any newly provided details; otherwise a new lead is created.
    """
    if payload.source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Must be one of: {', '.join(sorted(VALID_SOURCES))}",
        )

    email = str(payload.email).lower().strip()

    existing_query = select(Lead).where(Lead.email == email)
    existing_result = await session.execute(existing_query)
    lead = existing_result.scalar_one_or_none()
    is_new_lead = lead is None

    if lead:
        # PUBLIC endpoint: only FILL empty fields — never let an anonymous
        # POST overwrite what the pipeline already knows about a prospect.
        if payload.name and not lead.name:
            lead.name = payload.name
        if payload.organization_name and not lead.organization_name:
            lead.organization_name = payload.organization_name
        if payload.what_tried and not lead.what_tried:
            lead.what_tried = payload.what_tried
        lead.updated_at = datetime.utcnow()
    else:
        lead = Lead(
            email=email,
            name=payload.name,
            organization_name=payload.organization_name,
            source=payload.source,
            what_tried=payload.what_tried,
        )
        session.add(lead)

    await session.commit()

    # Instant acknowledgment for first-time website-form leads. Signups get
    # the welcome email instead; conference/manual entries are founder-typed,
    # so an automated "we saw your message" would be wrong there. Repeat
    # submitters are skipped so nobody can use us as an email cannon.
    # Must never block or fail the capture.
    if is_new_lead and payload.source in AUTO_ACK_SOURCES:
        from app.services.email import email_service

        try:
            email_service.send_lead_ack_email(to_email=email, lead_name=payload.name)
        except Exception:
            pass

        # And tell the founder — the lead's email is the whole point.
        try:
            email_service.send_lead_notification_email(
                lead_email=email,
                lead_name=payload.name,
                lead_org=payload.organization_name,
                source=payload.source,
                what_tried=payload.what_tried,
            )
        except Exception:
            pass

    # Write-only for the public: reflecting the stored lead would leak the
    # founder's internal notes and pipeline status to anyone posting an email.
    return {"ok": True}


@router.get("/leads", response_model=list[LeadResponse])
async def list_leads(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    source: Optional[str] = Query(default=None, description="Filter by source"),
    limit: int = Query(default=200, le=1000),
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(require_super_admin)] = None,
):
    """List leads, newest first. Admin only. Optional status/source filters."""
    query = select(Lead)

    if status:
        query = query.where(Lead.status == status)
    if source:
        query = query.where(Lead.source == source)

    query = query.order_by(Lead.created_at.desc()).limit(limit)

    result = await session.execute(query)
    leads = result.scalars().all()

    return [LeadResponse.from_lead(lead) for lead in leads]


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(require_super_admin)] = None,
):
    """Update a lead's status and/or notes. Admin only."""
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
            )
        lead.status = payload.status

    if payload.notes is not None:
        lead.notes = payload.notes

    lead.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(lead)

    return LeadResponse.from_lead(lead)


@router.post("/leads/{lead_id}/follow-up", response_model=LeadResponse)
async def send_follow_up(
    lead_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(require_super_admin)] = None,
):
    """Send the follow-up email to a lead and move it to 'contacted'. Admin only."""
    from app.services.email import email_service

    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    first_name = (lead.name or "").split(" ")[0] or "there"
    tried = f" on {lead.what_tried}" if lead.what_tried else ""
    ok = email_service.send_email(
        to_email=lead.email,
        subject="Your Climatrix results — and what they'd look like audit-ready",
        html_content=(
            f"<p>Hi {first_name},</p>"
            f"<p>Thanks for trying Climatrix{tried}. What you saw is the same engine "
            "our clients use to turn messy spreadsheets from finance, fleet and "
            "facilities into a defensible GHG inventory — every line marked "
            "<b>measured / calculated / estimated / gap</b>, with the factor and "
            "formula shown.</p>"
            "<p>If you'd like, I'll walk you through what your full Scope 1/2/3 "
            "picture would look like — 20 minutes, your data.</p>"
            "<p>Avi Luvchik<br/>Founder, Climatrix — climatrix.co</p>"
        ),
        text_content=(
            f"Hi {first_name},\n\nThanks for trying Climatrix{tried}. Happy to walk "
            "you through your full Scope 1/2/3 picture — 20 minutes, your data.\n\n"
            "Avi Luvchik, Founder — climatrix.co"
        ),
    )
    if not ok:
        raise HTTPException(status_code=502, detail="Email could not be sent")

    if lead.status == "new":
        lead.status = "contacted"
    stamp = datetime.utcnow().strftime("%Y-%m-%d")
    note = f"[{stamp}] follow-up email sent"
    lead.notes = f"{lead.notes}\n{note}" if lead.notes else note
    lead.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(lead)
    return LeadResponse.from_lead(lead)
