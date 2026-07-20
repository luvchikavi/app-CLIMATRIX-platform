"""Entitlements: resolve an organization's effective plan + limits, with lazy trial expiry.

Single place that decides what an org can do, so API endpoints just call a check and
return HTTP 402 (with a machine-readable code) when a limit is hit.

Trial semantics (the 14-day TEASER, GOING-LIVE-PLAN Wave 4): show the capability,
withhold the benefit. A trialing org runs the full parser + calculation engine and
sees results on screen, but gets no exports, one site/period/seat, and a capped
import volume. Expired trial falls back to FREE — data preserved, read-only-ish.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import Organization, User, SubscriptionPlan
from app.services.billing import PLAN_LIMITS, TRIAL_LIMITS

# Plans that unlock the workflow modules (CBAM register/declarations, decarbonization
# management). Trial and Starter see the teaser only. A Report Pass is Professional
# for its 90-day window.
_MODULE_PLANS = {
    SubscriptionPlan.PROFESSIONAL.value,
    SubscriptionPlan.ENTERPRISE.value,
    SubscriptionPlan.REPORT_PASS.value,
}


def _free_entitlement(*, expired: bool = False, org=None) -> dict:
    return {
        "effective_plan": SubscriptionPlan.FREE.value,
        "is_trialing": False,
        "is_expired": expired,
        "limits": dict(PLAN_LIMITS[SubscriptionPlan.FREE]),
        "trial_ends_at": (
            org.trial_ends_at.isoformat() if org and org.trial_ends_at else None
        ),
        "licensed_report_year": None,
        "plan_expires_at": None,
    }


def resolve_entitlement(org: Organization | None) -> dict:
    """Resolve effective plan + limits for an org, applying lazy expiry.

    - Active trial  -> TEASER limits (no exports, 1 site/period/seat, capped import).
    - Expired trial with no active paid sub -> effective FREE (read-only-ish).
    - Report Pass inside its window -> Professional-level limits, but exports
      licensed to ONE reporting year; past the window -> FREE (data preserved).
    - Otherwise -> the org's own plan limits, plus purchased add-ons
      (extra_sites / extra_users) stacked on the included caps.
    """
    if org is None:
        return _free_entitlement()

    try:
        plan = SubscriptionPlan(org.subscription_plan or "free")
    except ValueError:
        plan = SubscriptionPlan.FREE

    status = org.subscription_status or None
    now = datetime.utcnow()
    trialing = (
        status == "trialing"
        and org.trial_ends_at is not None
        and org.trial_ends_at > now
    )
    trial_expired = (
        status == "trialing"
        and org.trial_ends_at is not None
        and org.trial_ends_at <= now
    )
    has_active_paid = status == "active"

    licensed_year = None
    pass_expires = None
    if trialing:
        effective = SubscriptionPlan.PROFESSIONAL
        limits = dict(TRIAL_LIMITS)
    elif trial_expired and not has_active_paid:
        return _free_entitlement(expired=True, org=org)
    elif plan == SubscriptionPlan.REPORT_PASS:
        window_open = org.plan_expires_at is not None and org.plan_expires_at > now
        if not window_open:
            return _free_entitlement(expired=True, org=org)
        effective = plan
        limits = dict(PLAN_LIMITS[SubscriptionPlan.REPORT_PASS])
        licensed_year = org.licensed_report_year
        pass_expires = org.plan_expires_at
    else:
        effective = plan
        limits = dict(PLAN_LIMITS.get(plan, PLAN_LIMITS[SubscriptionPlan.FREE]))

    # Purchased add-ons stack on the included caps of any paid tier.
    if not trialing and effective not in (SubscriptionPlan.FREE,):
        for key, extra in (("users", org.extra_users), ("sites", org.extra_sites)):
            if extra and limits.get(key, -1) != -1:
                limits[key] = limits[key] + extra

    return {
        "effective_plan": effective.value,
        "is_trialing": trialing,
        "is_expired": trial_expired and not has_active_paid,
        "limits": limits,
        "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,
        "licensed_report_year": licensed_year,
        "plan_expires_at": pass_expires.isoformat() if pass_expires else None,
    }


async def get_entitlement(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """FastAPI dependency returning the current org's resolved entitlement."""
    org = await session.get(Organization, current_user.organization_id)
    return resolve_entitlement(org)


def _limit_error(limit_type: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=402,
        detail={
            "code": "limit_reached",
            "limit_type": limit_type,
            "message": message,
            "upgrade_url": "/pricing",
        },
    )


def _has_module_access(entitlement: dict) -> bool:
    return (
        not entitlement["is_trialing"]
        and entitlement["effective_plan"] in _MODULE_PLANS
    )


async def require_report_generation(
    entitlement: Annotated[dict, Depends(get_entitlement)],
) -> None:
    """Block formal report generation/export when the effective plan allows 0 reports.

    On the teaser trial this blocks every export — results stay on screen."""
    if entitlement["limits"].get("reports_per_month", 0) == 0:
        if entitlement["is_trialing"]:
            raise _limit_error(
                "exports",
                "Downloads and exports aren't included in the trial — your results "
                "stay on screen. Subscribe to export audit-ready reports.",
            )
        raise _limit_error(
            "reports",
            "Report generation isn't available on the Free plan. "
            "Start a trial or upgrade to generate audit-ready reports.",
        )


def ensure_period_year_licensed(entitlement: dict, period) -> None:
    """Report Pass orgs export only the reporting year their pass covers.

    Full subscribers (licensed_report_year is None) are unaffected. Periods
    without a start date can't be year-checked and pass through."""
    year = entitlement.get("licensed_report_year")
    if year is None or period is None or not getattr(period, "start_date", None):
        return
    if period.start_date.year != year:
        raise _limit_error(
            "report_pass_year",
            f"Your Report Pass covers reporting year {year}. Exports for other "
            "years need their own pass or an annual subscription.",
        )


async def require_export_for_period(
    period_id: UUID,
    entitlement: Annotated[dict, Depends(get_entitlement)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Export gate for period-scoped report endpoints: the plan-level export
    check plus the Report Pass year license. `period_id` binds from the
    route's own path/query parameter."""
    await require_report_generation(entitlement)
    if entitlement.get("licensed_report_year") is None:
        return
    from app.models.core import ReportingPeriod

    period = await session.get(ReportingPeriod, period_id)
    if period is not None and period.organization_id == current_user.organization_id:
        ensure_period_year_licensed(entitlement, period)


async def require_report_view(
    entitlement: Annotated[dict, Depends(get_entitlement)],
) -> None:
    """Allow on-screen report views for trial (the wow) and paid tiers; block only
    Free / expired-trial orgs."""
    if (
        entitlement["limits"].get("reports_per_month", 0) == 0
        and not entitlement["is_trialing"]
    ):
        raise _limit_error(
            "reports",
            "Your trial has ended — your data is safe. Subscribe to keep "
            "viewing and exporting reports.",
        )


async def require_cbam_workflow(
    entitlement: Annotated[dict, Depends(get_entitlement)],
) -> None:
    """CBAM screening stays open to everyone; the workflow (register, declarations,
    certificates, supplier requests, exports) is a paid Professional feature."""
    if not _has_module_access(entitlement):
        raise _limit_error(
            "cbam",
            "The CBAM register, declarations and supplier workflow are available "
            "on the Professional plan. Screening remains free.",
        )


async def require_decarb_management(
    entitlement: Annotated[dict, Depends(get_entitlement)],
) -> None:
    """Decarbonization targets/scenarios management is a paid Professional feature;
    trial sees the recommendations teaser only."""
    if not _has_module_access(entitlement):
        raise _limit_error(
            "decarbonization",
            "Decarbonization planning (targets, scenarios, full recommendations) "
            "is available on the Professional plan.",
        )


async def _count(session: AsyncSession, stmt) -> int:
    return int((await session.execute(stmt)).scalar_one() or 0)


async def require_site_capacity(
    entitlement: Annotated[dict, Depends(get_entitlement)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Block creating a site beyond the plan's cap (trial/free: 1)."""
    cap = entitlement["limits"].get("sites", -1)
    if cap == -1:
        return
    from app.models.core import Site

    existing = await _count(
        session,
        select(func.count())
        .select_from(Site)
        .where(Site.organization_id == current_user.organization_id),
    )
    if existing >= cap:
        raise _limit_error(
            "sites",
            f"Your plan includes {cap} site{'s' if cap != 1 else ''}. "
            "Upgrade to add more sites.",
        )


async def require_period_capacity(
    entitlement: Annotated[dict, Depends(get_entitlement)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Block creating a reporting period beyond the plan's cap (trial/free: 1)."""
    cap = entitlement["limits"].get("periods", -1)
    if cap == -1:
        return
    from app.models.core import ReportingPeriod

    existing = await _count(
        session,
        select(func.count())
        .select_from(ReportingPeriod)
        .where(ReportingPeriod.organization_id == current_user.organization_id),
    )
    if existing >= cap:
        raise _limit_error(
            "periods",
            f"Your plan includes {cap} reporting period"
            f"{'s' if cap != 1 else ''}. Upgrade to add more.",
        )


async def ensure_seat_capacity(session: AsyncSession, organization_id) -> None:
    """Raise 402 when inviting one more member would exceed the plan's seat cap.

    Counts active users + pending invitations. Called inline from the invite
    endpoint (auth.py) to avoid a module-level import cycle with app.api.auth."""
    from app.models.core import Invitation, InvitationStatus

    org = await session.get(Organization, organization_id)
    entitlement = resolve_entitlement(org)
    cap = entitlement["limits"].get("users", -1)
    if cap == -1:
        return
    users = await _count(
        session,
        select(func.count())
        .select_from(User)
        .where(
            User.organization_id == organization_id,
            User.is_active == True,  # noqa: E712
        ),
    )
    pending = await _count(
        session,
        select(func.count())
        .select_from(Invitation)
        .where(
            Invitation.organization_id == organization_id,
            Invitation.status == InvitationStatus.PENDING,
        ),
    )
    if users + pending >= cap:
        if entitlement["is_trialing"]:
            raise _limit_error(
                "users",
                "The trial is single-user. Subscribe to invite your team.",
            )
        raise _limit_error(
            "users",
            f"Your plan includes {cap} team member{'s' if cap != 1 else ''}. "
            "Upgrade to invite more.",
        )


async def ensure_import_file_capacity(
    session: AsyncSession, entitlement: dict, organization_id
) -> None:
    """Raise 402 when the org has used up its Smart Import upload allowance
    (trial: 3 files; free/expired: uploads closed)."""
    cap = entitlement["limits"].get("import_files", -1)
    if cap == -1:
        return
    from app.models.ingestion import IngestionSession

    if cap == 0:
        raise _limit_error(
            "import_files",
            "Your trial has ended — your data is safe. Subscribe to keep "
            "importing files.",
        )
    existing = await _count(
        session,
        select(func.count())
        .select_from(IngestionSession)
        .where(IngestionSession.organization_id == organization_id),
    )
    if existing >= cap:
        raise _limit_error(
            "import_files",
            f"The trial includes {cap} file imports — you've used them all. "
            "Subscribe for unlimited imports.",
        )


async def ensure_import_row_capacity(
    session: AsyncSession, entitlement: dict, organization_id, adding: int
) -> None:
    """Raise 402 when committing `adding` more rows would exceed the plan's
    committed-row allowance (trial: 500 rows total)."""
    cap = entitlement["limits"].get("import_rows", -1)
    if cap == -1:
        return
    from app.models.ingestion import IngestionSession

    committed = await _count(
        session,
        select(func.coalesce(func.sum(IngestionSession.committed_count), 0)).where(
            IngestionSession.organization_id == organization_id
        ),
    )
    if committed + adding > cap:
        raise _limit_error(
            "import_rows",
            f"The trial includes {cap} imported rows ({committed} used). "
            "Subscribe to commit the rest — nothing you staged is lost.",
        )
