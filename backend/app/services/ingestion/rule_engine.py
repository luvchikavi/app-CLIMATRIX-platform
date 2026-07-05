"""Compliance rule engine — deterministic legality checks on a proposed row.

Third grounding layer (after catalog retrieval + resolver/unit grounding). Uses
the factor catalog as the source of truth to catch an LLM (or human) assigning the
WRONG scope/category to an otherwise-valid activity_key — e.g. mapping a Scope-1
fuel key to Scope 2, or filing flights under 3.7 (commuting) instead of 3.6.
Also tags CBAM-covered goods. Violations carry the correct values so the review
UI can one-click fix them (human review is mandatory — nothing auto-commits).

No LLM, no DB — pure logic over the catalog. Cheap and testable.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.ingestion.catalog import FactorCatalog

# EU CBAM-covered goods (cement, iron & steel, aluminium, fertilisers, hydrogen).
CBAM_KEYWORDS = (
    "steel", "iron", "aluminum", "aluminium", "cement", "clinker",
    "fertiliser", "fertilizer", "ammonia", "nitric", "hydrogen",
)


@dataclass
class RuleViolation:
    rule: str
    message: str
    suggested_scope: int | None = None
    suggested_category: str | None = None


def is_cbam_good(activity_key: str) -> bool:
    """True if the activity looks like a CBAM-covered good (feeds the CBAM module)."""
    k = (activity_key or "").lower()
    return any(w in k for w in CBAM_KEYWORDS)


def scope_category_consistent(scope: int, category_code: str) -> bool:
    """A category code must live under its scope (e.g. '3.6' -> Scope 3)."""
    if not category_code:
        return True
    return category_code.split(".")[0] == str(scope)


def check_row(
    catalog: FactorCatalog,
    activity_key: str,
    scope: int,
    category_code: str,
) -> list[RuleViolation]:
    """Return legality violations for a proposed row. Empty list == clean.

    An unknown activity_key returns no rule violations here (it's already caught
    by the grounding/resolver layer)."""
    violations: list[RuleViolation] = []

    # 1. Scope <-> category prefix must be internally consistent.
    if not scope_category_consistent(scope, category_code):
        violations.append(
            RuleViolation(
                rule="scope_category_inconsistent",
                message=(
                    f"Category '{category_code}' cannot sit under Scope {scope} "
                    f"(a {category_code.split('.')[0]}.x category is Scope "
                    f"{category_code.split('.')[0]})."
                ),
                suggested_scope=int(category_code.split(".")[0])
                if category_code and category_code.split(".")[0].isdigit()
                else None,
                suggested_category=category_code,
            )
        )

    # 2. Match against the catalog's authoritative scope/category for this key.
    entry = catalog.get(activity_key)
    if entry is None:
        return violations

    if entry.scope and scope and entry.scope != scope:
        violations.append(
            RuleViolation(
                rule="scope_mismatch",
                message=(
                    f"'{activity_key}' is a Scope {entry.scope} activity, but it "
                    f"was mapped to Scope {scope}."
                ),
                suggested_scope=entry.scope,
                suggested_category=entry.category_code,
            )
        )

    if entry.category_code and category_code and entry.category_code != category_code:
        violations.append(
            RuleViolation(
                rule="category_mismatch",
                message=(
                    f"'{activity_key}' belongs to category {entry.category_code}, "
                    f"not {category_code}."
                ),
                suggested_scope=entry.scope,
                suggested_category=entry.category_code,
            )
        )

    return violations
