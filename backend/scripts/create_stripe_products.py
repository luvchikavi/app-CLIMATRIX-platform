"""Create (or reuse) the CLIMATRIX Stripe product catalog and print the price IDs.

Run this ONCE per Stripe mode (test, then live) after the account is active.
It is idempotent by product name: re-running finds the existing product and
only creates a price if one with the same amount/interval isn't already there.

Usage:
    STRIPE_SECRET_KEY=sk_test_xxx python -m scripts.create_stripe_products

Then copy the printed STRIPE_PRICE_* lines into the backend environment
(Railway → Variables), and set the webhook per docs/STRIPE_SETUP.md.

Mirrors app/services/billing.py PLAN_PRICING / ADDON_PRICING — keep in sync.
"""

import os
import sys

import stripe

# Amounts in USD cents. Mirrors billing.py (dollars) — the single source of
# truth for what customers pay.
CATALOG = [
    {
        "env": "STRIPE_PRICE_STARTER_MONTHLY",
        "product": "CLIMATRIX Starter",
        "amount": 9900,
        "recurring": {"interval": "month"},
        "nickname": "Starter Monthly",
    },
    {
        "env": "STRIPE_PRICE_STARTER_ANNUAL",
        "product": "CLIMATRIX Starter",
        "amount": 101000,
        "recurring": {"interval": "year"},
        "nickname": "Starter Annual",
    },
    {
        "env": "STRIPE_PRICE_PROFESSIONAL_ANNUAL",
        "product": "CLIMATRIX Professional",
        "amount": 356000,
        "recurring": {"interval": "year"},
        "nickname": "Professional Annual",
    },
    {
        "env": "STRIPE_PRICE_REPORT_PASS",
        "product": "CLIMATRIX Report Pass",
        "amount": 179000,
        "recurring": None,  # one-time
        "nickname": "Report Pass (one reporting year)",
    },
    {
        "env": "STRIPE_PRICE_SITE_PACK",
        "product": "CLIMATRIX Site Pack (+5 sites)",
        "amount": 49000,
        "recurring": {"interval": "year"},
        "nickname": "Site Pack Annual",
    },
    {
        "env": "STRIPE_PRICE_SEAT",
        "product": "CLIMATRIX Extra Seat",
        "amount": 19000,
        "recurring": {"interval": "year"},
        "nickname": "Extra Seat Annual",
    },
]


def _find_product(name: str):
    for p in stripe.Product.list(active=True, limit=100).auto_paging_iter():
        if p.name == name:
            return p
    return None


def _find_price(product_id: str, amount: int, recurring):
    for pr in stripe.Price.list(
        product=product_id, active=True, limit=100
    ).auto_paging_iter():
        if pr.unit_amount != amount or pr.currency != "usd":
            continue
        want_interval = recurring["interval"] if recurring else None
        have_interval = pr.recurring.interval if pr.recurring else None
        if want_interval == have_interval:
            return pr
    return None


def main() -> int:
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        print("ERROR: set STRIPE_SECRET_KEY (sk_test_… or sk_live_…)", file=sys.stderr)
        return 1
    stripe.api_key = key
    mode = "LIVE" if key.startswith("sk_live") else "TEST"
    print(f"# Stripe mode: {mode}\n")

    env_lines = []
    for item in CATALOG:
        product = _find_product(item["product"]) or stripe.Product.create(
            name=item["product"]
        )
        price = _find_price(product.id, item["amount"], item["recurring"])
        if price is None:
            kwargs = dict(
                product=product.id,
                unit_amount=item["amount"],
                currency="usd",
                nickname=item["nickname"],
            )
            if item["recurring"]:
                kwargs["recurring"] = item["recurring"]
            price = stripe.Price.create(**kwargs)
            status = "created"
        else:
            status = "reused"
        print(f"# {item['nickname']}: {status} {price.id}")
        env_lines.append(f"{item['env']}={price.id}")

    print("\n# --- Copy these into the backend environment (Railway) ---")
    print("\n".join(env_lines))
    print(
        "\n# Also set: STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, "
        "STRIPE_WEBHOOK_SECRET (from the webhook endpoint you create)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
