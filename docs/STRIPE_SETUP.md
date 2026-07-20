# Stripe setup — going live with the restructured catalog

The code is wired (branch `feat/stripe-wiring`). It stays inert until these
env vars are set, so it is safe to merge before Stripe is configured. Do the
**test-mode** pass first, verify end-to-end, then repeat for **live**.

## 1. Create the products & prices

From `platform/backend/`, with your **test** secret key:

```bash
STRIPE_SECRET_KEY=sk_test_xxx python -m scripts.create_stripe_products
```

It prints six `STRIPE_PRICE_*=price_…` lines. The script is idempotent — safe
to re-run; it reuses existing products/prices.

## 2. Set the backend environment (Railway → Variables)

```
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx          # from step 4
STRIPE_PRICE_STARTER_MONTHLY=price_...
STRIPE_PRICE_STARTER_ANNUAL=price_...
STRIPE_PRICE_PROFESSIONAL_ANNUAL=price_...
STRIPE_PRICE_REPORT_PASS=price_...
STRIPE_PRICE_SITE_PACK=price_...
STRIPE_PRICE_SEAT=price_...
```

Set `NEXT_PUBLIC_STRIPE_ENABLED=true` (or the publishable key) on the frontend
so the checkout buttons call the API instead of the sales mailto fallback.

## 3. Customer Portal

Stripe Dashboard → Settings → Billing → Customer portal → enable. This powers
the in-app "Manage subscription" button (`/api/billing/portal`).

## 4. Webhook

Stripe Dashboard → Developers → Webhooks → Add endpoint:

- URL: `https://<backend-domain>/api/billing/webhook`
- Events: `checkout.session.completed`, `customer.subscription.created`,
  `customer.subscription.updated`, `customer.subscription.deleted`
- Copy the signing secret → `STRIPE_WEBHOOK_SECRET`.

## What each purchase does

| Purchase | Checkout | On completion |
|---|---|---|
| Starter (monthly/annual) | `POST /api/billing/checkout` `{plan:"starter", cadence}` | subscription events set plan/status/period end; 14-day trial if first time |
| Professional (annual) | `POST /api/billing/checkout` `{plan:"professional", cadence:"annual"}` | same; monthly is rejected (annual-only) |
| Report Pass | `POST /api/billing/report-pass/checkout` `{report_year}` | one-time payment → plan=`report_pass`, `licensed_report_year`, `plan_expires_at`=+90d |
| Enterprise | — | sales-assisted (`mailto`) |

## Add-ons (site pack, extra seat) — phase 2

Prices are created by the script and ready, but in-app add-on checkout is not
wired yet. Until it is, grant capacity after payment via the super-admin
endpoint (no code change, audit-logged):

```
PATCH /api/admin/organizations/{org_id}/subscription
{ "extra_sites": 5 }      # one site pack
{ "extra_users": 1 }      # one seat
```

## Verify (test mode)

1. Subscribe a throwaway org to Professional (annual) with test card
   `4242 4242 4242 4242` → `/api/billing/subscription` shows
   `professional/active`.
2. Buy a Report Pass for 2025 → subscription shows `report_pass`,
   `licensed_report_year: 2025`, `plan_expires_at` ~90 days out; exporting a
   2025 report works, a 2024 report returns the 402 year-license message.
3. Cancel via the portal → webhook flips the org back toward free at period end.
