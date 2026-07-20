"""
Stripe billing service for subscription management.
Handles customer creation, subscription management, and webhook processing.
"""

import stripe
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.core import (
    Organization,
    SubscriptionPlan,
    SubscriptionStatus,
)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


# Plan limits (-1 = unlimited). reports_per_month gates formal report generation/export.
# import_files / import_rows cap the Smart Import funnel (uploads / committed rows).
PLAN_LIMITS = {
    SubscriptionPlan.FREE: {
        "activities_per_month": 50,
        "users": 1,
        "periods": 1,
        "sites": 1,
        "ai_extractions": 0,
        "reports_per_month": 0,  # preview only, no new report generation
        "export_formats": ["csv"],
        "import_files": 0,  # expired trial / free: data preserved, no new uploads
        "import_rows": 0,
    },
    SubscriptionPlan.STARTER: {
        "activities_per_month": 500,
        "users": 3,
        "periods": 4,
        "sites": 5,
        # Starter's concrete promise: the FULL AI parser for your own
        # operations — unlimited Smart Import for Scope 1 + 2. Scope 3 rows
        # are parsed and shown (the punch-list value) but commit-locked:
        # that's the Professional upsell, visible instead of vague.
        "ai_extractions": -1,
        "smart_import_scopes": [1, 2],
        "reports_per_month": 5,
        "export_formats": ["csv", "json", "pdf"],
        "import_files": -1,
        "import_rows": -1,
    },
    SubscriptionPlan.PROFESSIONAL: {
        "smart_import_scopes": [1, 2, 3],
        "activities_per_month": 5000,
        "users": 10,
        "periods": 12,
        "sites": 25,
        "ai_extractions": 100,
        "reports_per_month": -1,  # unlimited
        "export_formats": ["csv", "json", "cdp", "esrs"],
        "import_files": -1,
        "import_rows": -1,
    },
    SubscriptionPlan.ENTERPRISE: {
        "activities_per_month": -1,
        "users": -1,
        "periods": -1,
        "sites": -1,
        "ai_extractions": -1,
        "reports_per_month": -1,
        "export_formats": ["csv", "json", "cdp", "esrs", "custom"],
        "import_files": -1,
        "import_rows": -1,
    },
}

# Canonical pricing — the single source of truth the frontend mirrors.
# Annual totals are ~15% off the monthly rate.
TRIAL_DAYS = 14

# The 14-day TEASER trial (GOING-LIVE-PLAN Wave 4): the user sees the parser +
# calculation engine run on their own data, but gets no extractable deliverable —
# zero exports, single site/period/seat, capped import volume.
TRIAL_LIMITS = {
    "activities_per_month": 500,
    "users": 1,
    "periods": 1,
    "sites": 1,
    "ai_extractions": 100,
    "reports_per_month": 0,  # no exports of any kind during trial
    "export_formats": [],
    "import_files": 3,
    "import_rows": 500,
}

PLAN_PRICING = {
    SubscriptionPlan.FREE: {"monthly": 0, "annual": 0},
    SubscriptionPlan.STARTER: {"monthly": 99, "annual": 1010},
    SubscriptionPlan.PROFESSIONAL: {"monthly": 349, "annual": 3560},
    SubscriptionPlan.ENTERPRISE: {
        "monthly": None,
        "annual": None,
    },  # custom / Book a Demo
}


class BillingService:
    """Service for managing Stripe subscriptions."""

    @staticmethod
    def get_price_id_for_plan(plan: SubscriptionPlan) -> Optional[str]:
        """Get Stripe Price ID for a subscription plan."""
        price_map = {
            SubscriptionPlan.STARTER: settings.stripe_price_id_starter,
            SubscriptionPlan.PROFESSIONAL: settings.stripe_price_id_professional,
            SubscriptionPlan.ENTERPRISE: settings.stripe_price_id_enterprise,
        }
        return price_map.get(plan)

    @staticmethod
    async def create_customer(
        session: AsyncSession,
        organization: Organization,
        email: str,
    ) -> str:
        """Create a Stripe customer for an organization."""
        if organization.stripe_customer_id:
            return organization.stripe_customer_id

        customer = stripe.Customer.create(
            email=email,
            name=organization.name,
            metadata={
                "organization_id": str(organization.id),
            },
        )

        organization.stripe_customer_id = customer.id
        session.add(organization)
        await session.commit()

        return customer.id

    @staticmethod
    async def start_free_trial(
        session: AsyncSession,
        organization: Organization,
    ) -> None:
        """Start a 14-day free trial for a new organization without requiring Stripe.

        The trial grants Professional-tier access; entitlement resolution treats the
        org as Free once trial_ends_at passes with no active paid subscription.
        """
        organization.trial_ends_at = datetime.utcnow() + timedelta(days=14)
        organization.subscription_plan = SubscriptionPlan.PROFESSIONAL.value
        organization.subscription_status = SubscriptionStatus.TRIALING.value
        session.add(organization)
        await session.commit()

    @staticmethod
    async def create_checkout_session(
        session: AsyncSession,
        organization: Organization,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a Stripe Checkout session for subscription."""
        if not organization.stripe_customer_id:
            raise ValueError("Organization must have a Stripe customer ID")

        price_id = BillingService.get_price_id_for_plan(plan)
        if not price_id:
            raise ValueError(f"No price configured for plan: {plan}")

        checkout_session = stripe.checkout.Session.create(
            customer=organization.stripe_customer_id,
            mode="subscription",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            subscription_data={"trial_period_days": 14},
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "organization_id": str(organization.id),
                "plan": plan.value,
            },
        )

        return checkout_session.url

    @staticmethod
    async def create_portal_session(
        organization: Organization,
        return_url: str,
    ) -> str:
        """Create a Stripe Customer Portal session for managing subscription."""
        if not organization.stripe_customer_id:
            raise ValueError("Organization must have a Stripe customer ID")

        portal_session = stripe.billing_portal.Session.create(
            customer=organization.stripe_customer_id,
            return_url=return_url,
        )

        return portal_session.url

    @staticmethod
    async def cancel_subscription(
        session: AsyncSession,
        organization: Organization,
    ) -> bool:
        """Cancel an organization's subscription at period end."""
        if not organization.stripe_subscription_id:
            return False

        stripe.Subscription.modify(
            organization.stripe_subscription_id,
            cancel_at_period_end=True,
        )

        return True

    @staticmethod
    async def handle_subscription_updated(
        session: AsyncSession,
        subscription: stripe.Subscription,
    ) -> None:
        """Handle subscription update webhook event."""
        customer_id = subscription.customer

        # Find organization by Stripe customer ID
        result = await session.execute(
            select(Organization).where(Organization.stripe_customer_id == customer_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            return

        # Update subscription details (columns are String — always store .value)
        organization.stripe_subscription_id = subscription.id
        organization.subscription_status = SubscriptionStatus(subscription.status).value
        organization.subscription_current_period_end = datetime.fromtimestamp(
            subscription.current_period_end
        )

        # Determine plan from price
        if subscription.items.data:
            price_id = subscription.items.data[0].price.id
            if price_id == settings.stripe_price_id_starter:
                organization.subscription_plan = SubscriptionPlan.STARTER.value
            elif price_id == settings.stripe_price_id_professional:
                organization.subscription_plan = SubscriptionPlan.PROFESSIONAL.value
            elif price_id == settings.stripe_price_id_enterprise:
                organization.subscription_plan = SubscriptionPlan.ENTERPRISE.value

        session.add(organization)
        await session.commit()

    @staticmethod
    async def handle_subscription_deleted(
        session: AsyncSession,
        subscription: stripe.Subscription,
    ) -> None:
        """Handle subscription deletion webhook event."""
        customer_id = subscription.customer

        result = await session.execute(
            select(Organization).where(Organization.stripe_customer_id == customer_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            return

        # Reset to free plan
        organization.subscription_plan = SubscriptionPlan.FREE.value
        organization.subscription_status = SubscriptionStatus.CANCELED.value
        organization.stripe_subscription_id = None

        session.add(organization)
        await session.commit()

    @staticmethod
    async def handle_checkout_completed(
        session: AsyncSession,
        checkout_session: stripe.checkout.Session,
    ) -> None:
        """Handle checkout session completed webhook event."""
        org_id = checkout_session.metadata.get("organization_id")
        if not org_id:
            return

        result = await session.execute(
            select(Organization).where(Organization.id == UUID(org_id))
        )
        organization = result.scalar_one_or_none()

        if not organization:
            return

        # The subscription_updated event will handle the rest
        organization.stripe_customer_id = checkout_session.customer
        session.add(organization)
        await session.commit()

    @staticmethod
    def get_plan_limits(plan: SubscriptionPlan) -> dict:
        """Get limits for a subscription plan."""
        return PLAN_LIMITS.get(plan, PLAN_LIMITS[SubscriptionPlan.FREE])

    @staticmethod
    async def check_limit(
        session: AsyncSession,
        organization: Organization,
        limit_type: str,
        current_count: int,
    ) -> tuple[bool, int]:
        """
        Check if organization is within plan limits.
        Returns (is_within_limit, limit_value).
        """
        limits = BillingService.get_plan_limits(organization.subscription_plan)
        limit_value = limits.get(limit_type, 0)

        if limit_value == -1:  # Unlimited
            return True, -1

        return current_count < limit_value, limit_value
