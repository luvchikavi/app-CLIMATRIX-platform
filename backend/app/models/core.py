"""
Core domain models: Organization, User, Site, ReportingPeriod.
These form the multi-tenant foundation of the application.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String as SAString, Column as SAColumn
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.emission import Activity


class UserRole(str, Enum):
    """User roles for access control."""

    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class PeriodStatus(str, Enum):
    """Verification workflow status for reporting periods."""

    DRAFT = "draft"
    REVIEW = "review"
    SUBMITTED = "submitted"
    AUDIT = "audit"
    VERIFIED = "verified"
    LOCKED = "locked"


class AssuranceLevel(str, Enum):
    """Level of assurance for verified reports."""

    LIMITED = "limited"
    REASONABLE = "reasonable"


class SubscriptionPlan(str, Enum):
    """Subscription plans for billing.

    REPORT_PASS is the one-time product for once-a-year GHG reporters:
    Professional-level features for a 90-day window, licensed to a single
    reporting year (exports work only for periods of that year).
    """

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    REPORT_PASS = "report_pass"


class SubscriptionStatus(str, Enum):
    """Subscription status from Stripe."""

    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    UNPAID = "unpaid"


class InvitationStatus(str, Enum):
    """Status of a user invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELED = "canceled"


class OrganizationBase(SQLModel):
    """Base fields for Organization."""

    name: str = Field(max_length=255, index=True)
    country_code: Optional[str] = Field(default=None, max_length=2)
    industry_code: Optional[str] = Field(default=None, max_length=20)
    base_year: Optional[int] = Field(default=None)
    default_region: str = Field(default="Global", max_length=50)


class Organization(OrganizationBase, table=True):
    """
    Organization (tenant) model.
    All data is scoped to an organization for multi-tenancy.
    """

    __tablename__ = "organizations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Subscription/Billing fields
    stripe_customer_id: Optional[str] = Field(default=None, max_length=255, index=True)
    stripe_subscription_id: Optional[str] = Field(default=None, max_length=255)
    # Use sa_column with String to avoid native PostgreSQL ENUM type mismatch
    subscription_plan: str = Field(
        default="free",
        sa_column=SAColumn("subscription_plan", SAString(20), default="free"),
    )
    subscription_status: Optional[str] = Field(
        default=None,
        sa_column=SAColumn("subscription_status", SAString(20), nullable=True),
    )
    subscription_current_period_end: Optional[datetime] = Field(default=None)
    trial_ends_at: Optional[datetime] = Field(default=None)

    # Purchased add-ons on top of the plan's included caps (site packs / seats).
    # Stripe wiring updates these; super admin can grant them manually.
    extra_users: int = Field(default=0)
    extra_sites: int = Field(default=0)

    # Report Pass fields: which reporting year the pass covers, and when the
    # access window closes. Only meaningful when subscription_plan=report_pass.
    licensed_report_year: Optional[int] = Field(default=None)
    plan_expires_at: Optional[datetime] = Field(default=None)

    # Org setup gate: everything else in the app is locked until this is True
    # (server-validated via PATCH /organization/complete-setup).
    setup_complete: bool = Field(default=False)
    setup_completed_at: Optional[datetime] = Field(default=None)

    # Inventory profile (Layer 0 — formal facts every parse and report needs).
    # currency: ISO 4217, for spend-based data; unit_system disambiguates
    # "gal"/"ton"; consolidation_approach is the GHG Protocol boundary choice.
    currency: Optional[str] = Field(default=None, max_length=3)
    unit_system: str = Field(default="metric", max_length=10)  # metric | imperial
    consolidation_approach: str = Field(
        default="operational_control", max_length=30
    )  # operational_control | financial_control | equity_share

    # Base-year recalculation policy (GHG Protocol Corporate Standard ch. 5):
    # structural changes that shift the base-year total by more than this
    # percentage trigger a recalculation. Disclosed in every GHG report.
    recalculation_threshold_pct: float = Field(default=5.0)

    # Relationships
    users: list["User"] = Relationship(back_populates="organization")
    sites: list["Site"] = Relationship(back_populates="organization")
    reporting_periods: list["ReportingPeriod"] = Relationship(
        back_populates="organization"
    )


class UserBase(SQLModel):
    """Base fields for User."""

    email: str = Field(max_length=255, unique=True, index=True)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.VIEWER)
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    """
    User model with authentication and organization membership.
    """

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    hashed_password: Optional[str] = Field(default=None, max_length=255)
    google_id: Optional[str] = Field(default=None, max_length=255, index=True)
    onboarding_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    organization: Organization = Relationship(back_populates="users")


class Invitation(SQLModel, table=True):
    """
    User invitation for team members.
    Allows admins to invite new users to their organization.
    """

    __tablename__ = "invitations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    email: str = Field(max_length=255, index=True)
    role: UserRole = Field(default=UserRole.EDITOR)
    status: InvitationStatus = Field(default=InvitationStatus.PENDING)
    invited_by_id: UUID = Field(foreign_key="users.id")
    token: str = Field(max_length=255, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    accepted_at: Optional[datetime] = Field(default=None)

    # Relationships
    organization: Organization = Relationship()
    invited_by: User = Relationship()


class SiteBase(SQLModel):
    """Base fields for Site/Facility."""

    name: str = Field(max_length=255)
    country_code: Optional[str] = Field(default=None, max_length=2)
    address: Optional[str] = Field(default=None, max_length=500)
    grid_region: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)


class Site(SiteBase, table=True):
    """
    Site/Facility model for location-specific emissions tracking.
    """

    __tablename__ = "sites"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Seeded by "Load sample data"; removed wholesale by DELETE /sample-data
    is_demo: bool = Field(default=False)

    # Relationships
    organization: Organization = Relationship(back_populates="sites")
    activities: list["Activity"] = Relationship(back_populates="site")


class ReportingPeriodBase(SQLModel):
    """Base fields for ReportingPeriod."""

    name: str = Field(max_length=100)  # e.g., "Q1 2024", "FY 2024"
    start_date: date
    end_date: date
    is_locked: bool = Field(default=False)

    # Verification workflow fields
    status: PeriodStatus = Field(default=PeriodStatus.DRAFT)
    assurance_level: Optional[AssuranceLevel] = Field(default=None)


class ReportingPeriod(ReportingPeriodBase, table=True):
    """
    Reporting period for organizing activity data.
    Activities belong to a specific reporting period.

    Verification Workflow:
    DRAFT -> REVIEW -> SUBMITTED -> AUDIT -> VERIFIED -> LOCKED
    """

    __tablename__ = "reporting_periods"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Seeded by "Load sample data"; removed wholesale by DELETE /sample-data
    is_demo: bool = Field(default=False)

    # Verification tracking
    submitted_at: Optional[datetime] = Field(default=None)
    submitted_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    verified_at: Optional[datetime] = Field(default=None)
    verified_by: Optional[str] = Field(
        default=None, max_length=255
    )  # Auditor name/firm
    verification_statement: Optional[str] = Field(default=None)

    # Relationships
    organization: Organization = Relationship(back_populates="reporting_periods")
    activities: list["Activity"] = Relationship(back_populates="reporting_period")
    submitted_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ReportingPeriod.submitted_by_id]"}
    )


class VerifierAccess(SQLModel, table=True):
    """A scoped, read-only grant for an external verifier (VVB/auditor).

    The token IS the credential — no login. It unlocks exactly ONE reporting
    period's verification surface (inventory + per-line provenance + audit log
    + evidence package) for ONE organization, read-only, and nothing else.
    This isolation is why the verifier portal is a separate token-gated surface
    rather than a role inside the main app: there is no path from the token to
    another org, another period, or any write.
    """

    __tablename__ = "verifier_access"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    reporting_period_id: UUID = Field(foreign_key="reporting_periods.id", index=True)
    # Opaque URL-safe token, the sole credential for the portal.
    token: str = Field(max_length=64, unique=True, index=True)

    verifier_email: str = Field(max_length=255)
    verifier_name: Optional[str] = Field(default=None, max_length=255)  # person/firm

    # 'active' | 'revoked' — revocation is immediate (checked on every request).
    status: str = Field(default="active", max_length=20)

    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
    last_accessed_at: Optional[datetime] = Field(default=None)
    revoked_at: Optional[datetime] = Field(default=None)


class AuditAction(str, Enum):
    """Types of auditable actions."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    IMPORT = "import"
    EXPORT = "export"
    STATUS_CHANGE = "status_change"
    INVITE = "invite"
    PERMISSION_CHANGE = "permission_change"


class AuditLog(SQLModel, table=True):
    """
    Audit log for tracking all significant actions in the system.
    Used for compliance, debugging, and security monitoring.
    """

    __tablename__ = "audit_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True)
    user_email: Optional[str] = Field(default=None, max_length=255)

    # Action details
    action: AuditAction = Field(index=True)
    resource_type: str = Field(
        max_length=50, index=True
    )  # e.g., "activity", "period", "user"
    resource_id: Optional[str] = Field(
        default=None, max_length=100
    )  # ID of affected resource

    # Context
    description: str = Field(max_length=500)
    details: Optional[str] = Field(default=None)  # JSON string with additional details
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships (optional - for eager loading)
    organization: Organization = Relationship()
    user: Optional[User] = Relationship()


class ModuleWaitlist(SQLModel, table=True):
    """Waitlist signups for 'Coming Soon' modules (captures conference leads)."""

    __tablename__ = "module_waitlist"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(
        default=None, foreign_key="organizations.id", index=True
    )
    module_id: str = Field(max_length=50, index=True)
    email: str = Field(max_length=255, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
