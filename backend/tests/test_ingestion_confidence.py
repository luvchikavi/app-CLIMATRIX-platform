"""Tests for deterministic per-row confidence scoring (no DB, no LLM)."""
from app.services.ingestion.grounding import GroundingVerdict
from app.services.ingestion.confidence import score_row


def _g(resolved=True, unit_ok=True, cap=1.0, pcaf=3, reason="ok"):
    return GroundingVerdict(
        resolved=resolved,
        strategy="exact",
        factor_unit="kWh",
        unit_ok=unit_ok,
        needs_question=(not resolved) or (not unit_ok),
        confidence_cap=cap,
        pcaf_data_quality=pcaf,
        reason=reason,
    )


class _Violation:
    message = "scope mismatch"


def test_clean_exact_row_is_green_ready():
    v = score_row(_g(cap=1.0), [], llm_self_score=0.95)
    assert v.band == "green"
    assert v.status == "ready"
    assert v.confidence >= 0.85


def test_unresolved_is_zero_and_question():
    v = score_row(_g(resolved=False, cap=0.0), [], llm_self_score=0.99)
    assert v.confidence == 0.0
    assert v.band == "red"
    assert v.status == "needs_question"


def test_unit_mismatch_forces_low_confidence_question():
    v = score_row(_g(unit_ok=False, cap=0.4), [], llm_self_score=0.9)
    assert v.confidence <= 0.30
    assert v.status == "needs_question"


def test_rule_violation_caps_and_questions():
    v = score_row(_g(cap=1.0), [_Violation()], llm_self_score=0.95)
    assert v.confidence <= 0.50
    assert v.status == "needs_question"
    assert any("scope" in r for r in v.reasons)


def test_global_fallback_is_amber_review():
    # cap 0.70 * (0.4 + 0.6*0.9) = 0.658 -> amber band, below 0.75 -> needs_review
    v = score_row(_g(cap=0.70), [], llm_self_score=0.9)
    assert v.band == "amber"
    assert v.status == "needs_review"


def test_low_llm_score_pulls_confidence_down():
    high = score_row(_g(cap=1.0), [], llm_self_score=0.95).confidence
    low = score_row(_g(cap=1.0), [], llm_self_score=0.2).confidence
    assert low < high
