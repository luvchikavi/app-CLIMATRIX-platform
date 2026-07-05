"""Entitlements: resolve an organization's effective plan + limits, with lazy trial expiry.

Single place that decides what an org can do, so API endpoints just call a check and
return HTTP 402 (with a machine-readable code) when a limit is hit.
"""
from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import Organization, User, SubscriptionPlan
from app.services.billing import PLAN_LIMITS, TRIAL_REPORT_CAP


def resolve_entitlement(org: Organization | None) -> dict:
    """Resolve effective plan + limits for an org, applying lazy trial expiry.

    - Active trial  -> Professional-tier access, but reports capped to TRIAL_REPORT_CAP.
    - Expired trial with no active paid sub -> effective FREE (read-only-ish).
    - Otherwise -> the org's own plan limits.
    """
    if org is None:
        limits = dict(PLAN_LIMITS[SubscriptionPlan.FREE])
        return {
            "effective_plan": SubscriptionPlan.FREE.value,
            "is_trialing": False,
            "is_expired": False,
            "limits": limits,
            "trial_ends_at": None,
        }

    try:
        plan = SubscriptionPlan(org.subscription_plan or "free")
    except ValueError:
        plan = SubscriptionPlan.FREE

    status = org.subscription_status or None
    now = datetime.utcnow()
    trialing = status == "trialing" and org.trial_ends_at is not None and org.trial_ends_at > now
    trial_expired = (
        status == "trialing" and org.trial_ends_at is not None and org.trial_ends_at <= now
    )
    has_active_paid = status == "active"

    if trialing:
        effective = SubscriptionPlan.PROFESSIONAL
        limits = dict(PLAN_LIMITS[SubscriptionPlan.PROFESSIONAL])
        limits["reports_per_month"] = TRIAL_REPORT_CAP  # trial gets a capped taste
    elif trial_expired and not has_active_paid:
        effective = SubscriptionPlan.FREE
        limits = dict(PLAN_LIMITS[SubscriptionPlan.FREE])
    else:
        effective = plan
        limits = dict(PLAN_LIMITS.get(plan, PLAN_LIMITS[SubscriptionPlan.FREE]))

    return {
        "effective_plan": effective.value,
        "is_trialing": trialing,
        "is_expired": trial_expired and not has_active_paid,
        "limits": limits,
        "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,
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


async def require_report_generation(
    entitlement: Annotated[dict, Depends(get_entitlement)],
) -> None:
    """Block formal report generation when the effective plan allows 0 reports
    (Free tier / expired trial). Trial and paid tiers pass."""
    if entitlement["limits"].get("reports_per_month", 0) == 0:
        raise _limit_error(
            "reports",
            "Report generation isn't available on the Free plan. "
            "Start a trial or upgrade to generate audit-ready reports.",
        )
