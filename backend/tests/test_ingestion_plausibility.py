"""Tests for the plausibility layer (§4 of the verification spec)."""

from app.models.ingestion import RowStatus, StagedRow
from app.services.ingestion.plausibility import check_batch


def _row(key="electricity_kwh", qty=100.0, unit="kWh", status=RowStatus.READY):
    return StagedRow(
        activity_key=key,
        quantity=qty,
        unit=unit,
        status=status,
        confidence=0.9,
        band="green",
    )


def test_clean_batch_is_untouched():
    rows = [_row(qty=q) for q in (100, 120, 90, 110)]
    assert check_batch(rows) == 0
    assert all(r.band == "green" for r in rows)
    assert all(not (r.reasons or []) for r in rows)


def test_negative_and_zero_quantities_flagged():
    rows = [_row(qty=-5), _row(qty=0)]
    assert check_batch(rows) == 2
    assert "negative" in rows[0].reasons[0]
    assert rows[0].status == RowStatus.NEEDS_REVIEW
    assert "zero" in rows[1].reasons[0]


def test_magnitude_ceiling_catches_unit_slip():
    rows = [_row(qty=2_000_000_000, unit="kWh")]  # 2,000 GWh in one line
    assert check_batch(rows) == 1
    assert "unit slip" in rows[0].reasons[0]
    assert rows[0].band == "amber"
    assert rows[0].confidence <= 0.7


def test_batch_outlier_versus_siblings():
    rows = [_row(qty=q) for q in (100, 110, 95, 105)] + [_row(qty=90_000)]
    assert check_batch(rows) == 1
    outlier = rows[-1]
    assert "median" in outlier.reasons[0]
    assert outlier.status == RowStatus.NEEDS_REVIEW
    # siblings untouched
    assert all(not (r.reasons or []) for r in rows[:-1])


def test_prior_period_drift_flags_whole_group():
    rows = [_row(qty=q) for q in (5_000, 6_000, 5_500)]
    flagged = check_batch(rows, prior_totals={"electricity_kwh": 1_000})
    assert flagged == 3
    assert all("last period" in (r.reasons or [""])[-1] for r in rows)


def test_prior_period_within_range_not_flagged():
    rows = [_row(qty=q) for q in (400, 350, 380)]
    assert check_batch(rows, prior_totals={"electricity_kwh": 1_000}) == 0
