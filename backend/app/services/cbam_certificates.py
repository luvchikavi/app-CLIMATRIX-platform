"""
CBAM certificate ledger + 50% quarterly holding schedule (definitive regime).

The certificate account is a plain ledger of purchases, surrenders and
Commission repurchases (CBAMCertificateEntry rows). This module derives:

- The account summary: current holdings, totals per movement type, money
  spent and the weighted average purchase price.
- The Omnibus 50% quarterly holding schedule (Reg. (EU) 2025/2083): at each
  quarter end the declarant must hold certificates covering at least 50% of
  the embedded emissions of goods imported since the start of the year. The
  rule is practically relevant from 2027 — certificates for 2026 imports
  only go on sale 1 Feb 2027 and are surrendered with the 30 Sep 2027
  declaration — so 2026 rows are marked `not_applicable`.
- Key milestones for a compliance year (sales open, surrender deadline,
  repurchase request deadline).

Pure module: callers load ledger entries and the per-line emissions of the
year's imports (from the annual-declaration draft builder, so default lines
carry the year markup and supplier actuals are honoured) and pass them in;
nothing here touches the database.
"""

from datetime import date
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Optional, Sequence

ENTRY_TYPES = ("purchase", "surrender", "repurchase")

HOLDING_SHARE = Decimal("0.50")
HOLDING_RULE_START_YEAR = 2027
CERTIFICATE_SALES_OPEN = date(2027, 2, 1)

HOLDING_BASIS_ASSUMPTION = (
    "The 50% quarterly holding requirement is computed on the embedded "
    "emissions of the year's imports as calculated for the annual "
    "declaration (default-value lines include the Omnibus year markup; "
    "supplier-submitted actuals are honoured), cumulated by import date. "
    "The implementing rules may refine the exact basis — treat the "
    "schedule as a planning estimate."
)


def _q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _q3(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _signed_quantity(entry) -> int:
    """Purchases add to holdings; surrenders and repurchases remove."""
    return entry.quantity if entry.entry_type == "purchase" else -entry.quantity


def entry_total_eur(
    quantity: int, unit_price_eur: Optional[Decimal]
) -> Optional[Decimal]:
    """Ledger row total: quantity x unit price (None when no price given)."""
    if unit_price_eur is None:
        return None
    return _q2(Decimal(quantity) * unit_price_eur)


def running_balance_violation(entries: Sequence) -> Optional[str]:
    """
    Check that the ledger never goes negative in date order.

    Returns a human-readable violation message, or None when the ledger is
    consistent. Entries on the same date are netted together (purchases
    first), so a same-day purchase+surrender pair is fine.
    """
    balance = 0
    by_date: dict[date, int] = {}
    for entry in entries:
        by_date.setdefault(entry.entry_date, 0)
        by_date[entry.entry_date] += _signed_quantity(entry)

    for entry_date in sorted(by_date):
        balance += by_date[entry_date]
        if balance < 0:
            return (
                f"The ledger would go negative on {entry_date.isoformat()} "
                f"({balance} certificates): you cannot surrender or return "
                "more certificates than you hold on that date."
            )
    return None


def ledger_summary(entries: Sequence) -> dict:
    """Account summary across all ledger entries."""
    purchased = surrendered = repurchased = 0
    spent = Decimal("0")
    received = Decimal("0")
    priced_purchase_qty = 0
    priced_purchase_eur = Decimal("0")

    for entry in entries:
        total = (
            entry.total_eur
            if entry.total_eur is not None
            else entry_total_eur(entry.quantity, entry.unit_price_eur)
        )
        if entry.entry_type == "purchase":
            purchased += entry.quantity
            if total is not None:
                spent += total
                priced_purchase_qty += entry.quantity
                priced_purchase_eur += total
        elif entry.entry_type == "surrender":
            surrendered += entry.quantity
        elif entry.entry_type == "repurchase":
            repurchased += entry.quantity
            if total is not None:
                received += total

    weighted_avg = (
        _q2(priced_purchase_eur / priced_purchase_qty) if priced_purchase_qty else None
    )

    return {
        "balance": purchased - surrendered - repurchased,
        "purchased": purchased,
        "surrendered": surrendered,
        "repurchased": repurchased,
        "total_spent_eur": _q2(spent),
        "total_repurchased_eur": _q2(received),
        "weighted_avg_purchase_price_eur": weighted_avg,
    }


def _quarter_ends(year: int) -> list[date]:
    return [
        date(year, 3, 31),
        date(year, 6, 30),
        date(year, 9, 30),
        date(year, 12, 31),
    ]


def quarterly_holding_schedule(
    year: int,
    line_emissions: Sequence[tuple[date, Decimal]],
    entries: Sequence,
    ets_price_eur: Decimal,
    today: date,
) -> dict:
    """
    Build the 50% quarterly holding schedule for one compliance year.

    `line_emissions` are (import_date, embedded_emissions_tco2e) pairs for
    the year's imports — taken from the annual-declaration draft lines so
    markup/supplier logic is applied exactly once, in one place.

    Statuses per quarter: `met` (holdings cover the requirement),
    `shortfall` (they don't and the quarter end has passed — or is the
    current quarter), `upcoming` (future quarter), `not_applicable`
    (years before HOLDING_RULE_START_YEAR).
    """
    applies = year >= HOLDING_RULE_START_YEAR

    quarters = []
    for idx, q_end in enumerate(_quarter_ends(year), start=1):
        cumulative = Decimal("0")
        for import_date, emissions in line_emissions:
            if import_date <= q_end:
                cumulative += emissions

        required = (
            int((cumulative * HOLDING_SHARE).to_integral_value(rounding=ROUND_CEILING))
            if applies
            else 0
        )

        held = 0
        for entry in entries:
            if entry.entry_date <= q_end:
                held += _signed_quantity(entry)

        shortfall = max(0, required - held) if applies else 0

        if not applies:
            status = "not_applicable"
        elif q_end < today or (
            q_end.year == today.year and idx == _current_quarter(today)
        ):
            status = "met" if shortfall == 0 else "shortfall"
        else:
            status = "upcoming"

        quarters.append(
            {
                "quarter": idx,
                "quarter_end": q_end,
                "cumulative_emissions_tco2e": _q3(cumulative),
                "required_certificates": required,
                "held_certificates": held,
                "shortfall": shortfall,
                "estimated_topup_cost_eur": _q2(Decimal(shortfall) * ets_price_eur),
                "status": status,
            }
        )

    return {"applies": applies, "quarters": quarters}


def _current_quarter(today: date) -> int:
    return (today.month - 1) // 3 + 1


def milestones(year: int, today: date) -> list[dict]:
    """Key certificate dates for a compliance year, flagged past/future."""
    items = []
    if year == 2026:
        items.append(
            {
                "date": CERTIFICATE_SALES_OPEN,
                "label": (
                    "Certificate sales open on the central platform "
                    "(covering 2026 imports retroactively)"
                ),
            }
        )
    items.append(
        {
            "date": date(year + 1, 9, 30),
            "label": (
                f"Annual CBAM declaration for {year} due — certificates "
                "surrendered with the declaration"
            ),
        }
    )
    items.append(
        {
            "date": date(year + 1, 10, 31),
            "label": (
                "Deadline to request Commission repurchase of excess " "certificates"
            ),
        }
    )
    return [{**m, "passed": m["date"] < today} for m in items]
