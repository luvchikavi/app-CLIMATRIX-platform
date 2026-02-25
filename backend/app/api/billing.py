"""
Billing API endpoints for subscription management.
"""
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.database import get_session
from app.models.core import Organization, User, SubscriptionPlan
from app.api.auth import get_current_user
from app.services.billing import BillingService, PLAN_LIMITS


router = APIRouter(prefix="/billing", tags=["Billing"])


class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session."""
    plan: SubscriptionPlan
    success_url: str
    cancel_url: str


class CreatePortalRequest(BaseModel):
    """Request to create a customer portal session."""
    return_url: str


class SubscriptionResponse(BaseModel):
    """Current subscription details."""
    plan: str
    status: str | None
    current_period_end: str | None
    trial_ends_at: str | None
    is_trialing: bool
    plan_limits: dict


class CheckoutResponse(BaseModel):
    """Checkout session URL."""
    url: str


class PortalResponse(BaseModel):
    """Portal session URL."""
    url: str


class PlansResponse(BaseModel):
    """Available subscription plans."""
    plans: list[dict]


@router.get("/config")
async def get_billing_config():
    """Get Stripe publishable key for frontend."""
    return {"publishable_key": settings.stripe_publishable_key}


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current organization's subscription details."""
    result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    return SubscriptionResponse(
        plan=organization.subscription_plan.value,
        status=organization.subscription_status.value if organization.subscription_status else None,
        current_period_end=organization.subscription_current_period_end.isoformat() if organization.subscription_current_period_end else None,
        trial_ends_at=organization.trial_ends_at.isoformat() if organization.trial_ends_at else None,
        is_trialing=organization.trial_ends_at is not None and organization.subscription_status and organization.subscription_status.value == "trialing",
        plan_limits=BillingService.get_plan_limits(organization.subscription_plan),
    )


@router.get("/plans", response_model=PlansResponse)
async def get_plans():
    """Get available subscription plans and their features."""
    plans = []

    for plan in SubscriptionPlan:
        limits = PLAN_LIMITS.get(plan, {})
        plans.append({
            "id": plan.value,
            "name": plan.value.title(),
            "limits": limits,
            "price_monthly": {
                SubscriptionPlan.FREE: 0,
                SubscriptionPlan.STARTER: 49,
                SubscriptionPlan.PROFESSIONAL: 199,
                SubscriptionPlan.ENTERPRISE: None,  # Custom pricing
            }.get(plan),
            "features": _get_plan_features(plan),
        })

    return PlansResponse(plans=plans)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a Stripe Checkout session for upgrading subscription."""
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=503,
            detail="Billing is not configured",
        )

    result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Create Stripe customer if needed
    if not organization.stripe_customer_id:
        await BillingService.create_customer(
            session, organization, current_user.email
        )

    try:
        url = await BillingService.create_checkout_session(
            session=session,
            organization=organization,
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
        return CheckoutResponse(url=url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    request: CreatePortalRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a Stripe Customer Portal session for managing subscription."""
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=503,
            detail="Billing is not configured",
        )

    result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not organization.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account found. Please upgrade your plan first.",
        )

    try:
        url = await BillingService.create_portal_session(
            organization=organization,
            return_url=request.return_url,
        )
        return PortalResponse(url=url)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Cancel the current subscription at period end."""
    result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not organization.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription")

    try:
        success = await BillingService.cancel_subscription(session, organization)
        if success:
            return {"message": "Subscription will be canceled at period end"}
        raise HTTPException(status_code=400, detail="Failed to cancel subscription")
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event.type == "checkout.session.completed":
        await BillingService.handle_checkout_completed(session, event.data.object)
    elif event.type == "customer.subscription.created":
        await BillingService.handle_subscription_updated(session, event.data.object)
    elif event.type == "customer.subscription.updated":
        await BillingService.handle_subscription_updated(session, event.data.object)
    elif event.type == "customer.subscription.deleted":
        await BillingService.handle_subscription_deleted(session, event.data.object)

    return {"received": True}


def _get_plan_features(plan: SubscriptionPlan) -> list[str]:
    """Get feature list for a plan."""
    base_features = [
        "GHG Protocol compliance",
        "Carbon footprint calculation",
        "Basic reporting",
    ]

    if plan == SubscriptionPlan.FREE:
        return base_features + [
            "50 activities/month",
            "1 user",
            "CSV export",
        ]
    elif plan == SubscriptionPlan.STARTER:
        return base_features + [
            "500 activities/month",
            "Up to 3 users",
            "5 sites",
            "AI-powered data extraction",
            "JSON export",
        ]
    elif plan == SubscriptionPlan.PROFESSIONAL:
        return base_features + [
            "5,000 activities/month",
            "Up to 10 users",
            "25 sites",
            "100 AI extractions/month",
            "CDP & ESRS export",
            "Verification workflow",
            "Priority support",
        ]
    elif plan == SubscriptionPlan.ENTERPRISE:
        return base_features + [
            "Unlimited activities",
            "Unlimited users",
            "Unlimited sites",
            "Unlimited AI extractions",
            "Custom export formats",
            "CBAM compliance",
            "SSO integration",
            "Dedicated support",
            "SLA guarantee",
        ]

    return base_features
