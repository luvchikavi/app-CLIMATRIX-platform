"""Deterministic per-row confidence scoring.

The final confidence is COMPUTED from hard signals (how the factor resolved, unit
compatibility, compliance-rule violations) blended with the LLM's self-score — it
is never the LLM's self-report alone. Produces a 0..1 confidence, a green/amber/red
band, and a review status the funnel sorts by.

Owner-locked bands: green >= 0.85, amber 0.60-0.85, red < 0.60 (needs_review < 0.75).
Human review is mandatory on every import, so 'ready' rows are still shown for a
final approval — the band just orders the review grid.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.services.ingestion.grounding import GroundingVerdict

GREEN = 0.85
AMBER = 0.60
REVIEW = 0.75


@dataclass
class RowVerdict:
    confidence: float
    band: str  # "green" | "amber" | "red"
    status: str  # "ready" | "needs_review" | "needs_question"
    pcaf_data_quality: int
    reasons: list[str] = field(default_factory=list)


def _band(confidence: float) -> str:
    if confidence >= GREEN:
        return "green"
    if confidence >= AMBER:
        return "amber"
    return "red"


def score_row(
    grounding: GroundingVerdict,
    rule_violations: list | None = None,
    llm_self_score: float = 0.8,
) -> RowVerdict:
    """Combine hard grounding signals + rule checks + the LLM's self-score into a
    final verdict. A row that isn't grounded, whose unit can't be reconciled, or
    that breaks a compliance rule always drops to a question — regardless of how
    confident the LLM claims to be."""
    rule_violations = rule_violations or []
    reasons: list[str] = []
    llm = max(0.0, min(1.0, llm_self_score))

    # Base = the ceiling set by how the factor resolved, blended with LLM self-score.
    confidence = grounding.confidence_cap * (0.4 + 0.6 * llm)

    if not grounding.resolved:
        confidence = 0.0
        reasons.append(grounding.reason)
    elif not grounding.unit_ok:
        confidence = min(confidence, 0.30)
        reasons.append(grounding.reason)

    if rule_violations:
        confidence = min(confidence, 0.50)
        reasons.extend(getattr(v, "message", str(v)) for v in rule_violations)

    confidence = round(max(0.0, min(1.0, confidence)), 3)
    band = _band(confidence)

    if grounding.needs_question or not grounding.resolved or not grounding.unit_ok or rule_violations:
        status = "needs_question"
    elif confidence < REVIEW:
        status = "needs_review"
    else:
        status = "ready"

    if not reasons:
        reasons.append(grounding.reason)

    return RowVerdict(
        confidence=confidence,
        band=band,
        status=status,
        pcaf_data_quality=grounding.pcaf_data_quality,
        reasons=reasons,
    )
