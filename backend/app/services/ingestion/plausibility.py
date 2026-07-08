"""Plausibility checks — the sanity layer of the verification spec (§4).

Runs AFTER staging, over the whole batch, because outliers are only visible in
context: a 6,000,000 kWh row is fine for a steel mill and absurd next to eleven
sibling rows of ~5,000 kWh. Three deterministic checks, no LLM:

1. Nonsense values — negative or zero quantities.
2. Absolute-magnitude ceilings per unit family — catches unit slips
   (kWh entered as Wh, tonnes entered as kg) that grounding can't see because
   the unit itself is valid.
3. Batch outliers — a row wildly larger than the median of its own
   activity_key group in the same upload.
4. Prior-period drift — this upload's total for an activity_key is far from
   what the same organization committed last period (needs DB priors, passed in).

Flags never block: they append a human-readable reason and demote READY rows to
NEEDS_REVIEW so the practitioner's eye lands on them first.
"""

from __future__ import annotations

from statistics import median

from app.models.ingestion import RowStatus, StagedRow

# Ceilings per unit family — intentionally generous: they exist to catch
# thousand-fold unit slips, not to police big organizations.
_MAGNITUDE_CEILINGS: dict[str, tuple[float, str]] = {
    "kwh": (500_000_000, "electricity above 500 GWh in one line"),
    "mwh": (500_000, "electricity above 500 GWh in one line"),
    "liters": (50_000_000, "more than 50M liters in one line"),
    "litres": (50_000_000, "more than 50M liters in one line"),
    "l": (50_000_000, "more than 50M liters in one line"),
    "kg": (100_000_000, "more than 100,000 tonnes entered in kg"),
    "tonnes": (10_000_000, "more than 10M tonnes in one line"),
    "tonne": (10_000_000, "more than 10M tonnes in one line"),
    "t": (10_000_000, "more than 10M tonnes in one line"),
    "km": (50_000_000, "more than 50M km in one line"),
    "tonne-km": (1_000_000_000, "more than 1B tonne-km in one line"),
    "m3": (100_000_000, "more than 100M m³ in one line"),
    "nights": (1_000_000, "more than 1M hotel nights in one line"),
}

# Batch outlier: quantity > this × median of its activity_key group.
_OUTLIER_FACTOR = 50.0
_OUTLIER_MIN_GROUP = 3

# Prior-period drift: flag when total is more than this × prior (or under 1/x).
_DRIFT_FACTOR = 5.0


def _unit_family(unit: str | None) -> str:
    return (unit or "").strip().lower().split()[0] if unit and unit.strip() else ""


def check_batch(
    rows: list[StagedRow],
    prior_totals: dict[str, float] | None = None,
) -> int:
    """Annotate implausible rows in place; returns how many rows were flagged.

    ``prior_totals``: activity_key -> total quantity committed in the most
    recent PRIOR reporting period of the same organization (empty for a first
    period — drift is then simply not checked).
    """
    flagged = 0

    # Group by activity_key for outlier + drift checks
    groups: dict[str, list[StagedRow]] = {}
    for r in rows:
        if r.activity_key and r.quantity is not None:
            groups.setdefault(r.activity_key, []).append(r)

    def flag(row: StagedRow, reason: str) -> None:
        nonlocal flagged
        reasons = list(row.reasons or [])
        if reason in reasons:
            return
        reasons.append(reason)
        row.reasons = reasons
        row.confidence = min(row.confidence, 0.7)
        if row.status in (RowStatus.READY, RowStatus.READY.value):
            row.status = RowStatus.NEEDS_REVIEW
        if row.band == "green":
            row.band = "amber"
        flagged += 1

    # 1 + 2: per-row value sanity
    for r in rows:
        if r.quantity is None:
            continue
        if r.quantity < 0:
            flag(r, "Plausibility: quantity is negative — a credit/refund line? "
                    "Confirm before it subtracts from the inventory.")
        elif r.quantity == 0:
            flag(r, "Plausibility: quantity is zero — this line adds nothing; "
                    "delete it or fill the real amount.")
        else:
            ceiling = _MAGNITUDE_CEILINGS.get(_unit_family(r.unit))
            if ceiling and r.quantity > ceiling[0]:
                flag(r, f"Plausibility: {ceiling[1]} — check for a unit slip "
                        f"(value {r.quantity:,.0f} {r.unit}).")

    # 3: batch outliers within each activity group
    for key, group in groups.items():
        positives = [r.quantity for r in group if r.quantity and r.quantity > 0]
        if len(positives) < _OUTLIER_MIN_GROUP:
            continue
        med = median(positives)
        if med <= 0:
            continue
        for r in group:
            if r.quantity and r.quantity > med * _OUTLIER_FACTOR:
                flag(r, f"Plausibility: {r.quantity:,.0f} {r.unit or ''} is "
                        f">{_OUTLIER_FACTOR:.0f}× the median of its {len(positives)} "
                        f"sibling rows ({med:,.0f}) — outlier or unit slip?")

    # 4: drift vs the prior period
    for key, prior in (prior_totals or {}).items():
        group = groups.get(key)
        if not group or prior <= 0:
            continue
        total = sum(r.quantity for r in group if r.quantity and r.quantity > 0)
        if total <= 0:
            continue
        ratio = total / prior
        if ratio > _DRIFT_FACTOR or ratio < 1 / _DRIFT_FACTOR:
            direction = "higher" if ratio > 1 else "lower"
            for r in group:
                flag(r, f"Consistency: this upload totals {total:,.0f} for this "
                        f"activity vs {prior:,.0f} committed last period — "
                        f"{max(ratio, 1 / ratio):.0f}× {direction}. Real change, "
                        "or double-counting/missing data?")

    return flagged
