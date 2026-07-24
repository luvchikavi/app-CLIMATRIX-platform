"""
CRM / lead-management models.

Lightweight lead capture for follow-up: people who try the app, leave
details at a conference, sign up, or come from forums.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class Lead(SQLModel, table=True):
    """A captured lead for sales/marketing follow-up."""

    __tablename__ = "leads"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: Optional[str] = Field(default=None, max_length=255)
    email: str = Field(max_length=255, index=True)
    organization_name: Optional[str] = Field(default=None, max_length=255)

    # Where the lead came from:
    # "website_tryit" | "conference" | "signup" | "forum" | "manual"
    source: str = Field(max_length=50, index=True)

    # Follow-up status: "new" | "contacted" | "trial" | "customer" | "lost"
    status: str = Field(default="new", max_length=20, index=True)

    notes: Optional[str] = Field(default=None)
    # e.g. filename they demo-uploaded when trying the app
    what_tried: Optional[str] = Field(default=None, max_length=255)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None)

    # When the uncontacted-lead reminder was sent to the founder (once per lead)
    reminder_sent_at: Optional[datetime] = Field(default=None)
