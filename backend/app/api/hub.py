"""Data Hub API — the inventory profile and the coverage matrix.

The hub is the single home of data collection: the client declares per GHG
category what is relevant and where the data comes from (the profile), and the
matrix shows what has actually arrived against that expectation (coverage,
computed live from staged rows + committed activities — never stored).
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User
from app.models.emission import Activity, Emission
from app.models.hub import (
    CategoryProfile,
    CategoryRelevance,
    ExpectedDataForm,
    GHG_CATEGORIES,
    CATEGORY_BY_CODE,
    HUB_CODE_FOR,
)
from app.models.ingestion import (
    ClarificationQuestion,
    IngestionSession,
    RowStatus,
    StagedRow,
)

router = APIRouter()

MEASUREMENT_TIERS = ("measured", "calculated", "estimated", "gap")


# ============================================================================
# Schemas
# ============================================================================


class ProfileEntry(BaseModel):
    """One category's profile answers (write shape)."""

    category_code: str
    relevance: str
    exclusion_reason: str | None = None
    calculate_this_period: bool = True
    data_owner: str | None = None
    expected_form: str | None = None
    details: dict | None = None


class ProfileUpsert(BaseModel):
    """Bulk profile save — the whole matrix (or any subset) in one call."""

    site_id: UUID | None = None
    entries: list[ProfileEntry]


class ProfileEntryResponse(ProfileEntry):
    scope: int
    site_id: str | None = None
    updated_at: datetime | None = None


class CategoryCoverage(BaseModel):
    """What actually arrived for one category (computed, never stored)."""

    committed_count: int = 0
    total_co2e_kg: float = 0.0
    staged_count: int = 0
    staged_by_tier: dict[str, int] = {}
    open_questions: int = 0


class HubCategory(BaseModel):
    """One row of the hub matrix: expectation (profile) vs reality (coverage)."""

    scope: int
    code: str
    name: str
    description: str
    profile: ProfileEntryResponse | None = None
    coverage: CategoryCoverage


class HubStats(BaseModel):
    """Header strip numbers for the hub."""

    total_categories: int
    relevant: int
    not_relevant: int
    not_sure: int
    with_data: int  # relevant categories that have at least one row/activity
    open_questions: int


class HubOverview(BaseModel):
    categories: list[HubCategory]
    stats: HubStats


# ============================================================================
# Canonical category list
# ============================================================================


@router.get("/hub/categories")
async def list_hub_categories():
    """The canonical GHG category matrix (all scopes, always all rows)."""
    return GHG_CATEGORIES


# ============================================================================
# Profile
# ============================================================================


def _entry_response(p: CategoryProfile) -> ProfileEntryResponse:
    return ProfileEntryResponse(
        category_code=p.category_code,
        relevance=(
            p.relevance.value
            if isinstance(p.relevance, CategoryRelevance)
            else p.relevance
        ),
        exclusion_reason=p.exclusion_reason,
        calculate_this_period=p.calculate_this_period,
        data_owner=p.data_owner,
        expected_form=(
            p.expected_form.value
            if isinstance(p.expected_form, ExpectedDataForm)
            else p.expected_form
        ),
        details=p.details,
        scope=p.scope,
        site_id=str(p.site_id) if p.site_id else None,
        updated_at=p.updated_at,
    )


async def _load_profiles(
    session: AsyncSession, organization_id: UUID, site_id: UUID | None
) -> dict[str, CategoryProfile]:
    query = select(CategoryProfile).where(
        CategoryProfile.organization_id == organization_id,
        (
            CategoryProfile.site_id == site_id
            if site_id
            else CategoryProfile.site_id.is_(None)
        ),
    )
    rows = (await session.execute(query)).scalars().all()
    return {p.category_code: p for p in rows}


@router.get("/hub/profile", response_model=list[ProfileEntryResponse])
async def get_profile(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    site_id: UUID | None = None,
):
    """The saved profile rows (org-level by default; per-site when site_id given)."""
    profiles = await _load_profiles(session, current_user.organization_id, site_id)
    return [_entry_response(p) for p in profiles.values()]


@router.put("/hub/profile", response_model=list[ProfileEntryResponse])
async def upsert_profile(
    data: ProfileUpsert,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Bulk upsert of profile rows, keyed by (org, site_id, category_code)."""
    if current_user.role.value not in ["editor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=403, detail="Viewers cannot edit the inventory profile"
        )

    valid_relevance = {r.value for r in CategoryRelevance}
    valid_forms = {f.value for f in ExpectedDataForm}
    errors: list[str] = []
    for e in data.entries:
        if e.category_code not in CATEGORY_BY_CODE:
            errors.append(f"Unknown category '{e.category_code}'")
            continue
        if e.relevance not in valid_relevance:
            errors.append(f"{e.category_code}: invalid relevance '{e.relevance}'")
        if e.relevance == CategoryRelevance.NOT_RELEVANT.value and not (
            e.exclusion_reason and e.exclusion_reason.strip()
        ):
            errors.append(
                f"{e.category_code}: 'not relevant' needs a reason "
                "(the documented exclusion an auditor will read)"
            )
        if e.expected_form and e.expected_form not in valid_forms:
            errors.append(f"{e.category_code}: invalid form '{e.expected_form}'")
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    existing = await _load_profiles(session, current_user.organization_id, data.site_id)
    now = datetime.utcnow()
    saved: list[CategoryProfile] = []
    for e in data.entries:
        cat = CATEGORY_BY_CODE[e.category_code]
        reason = (
            e.exclusion_reason
            if e.relevance == CategoryRelevance.NOT_RELEVANT.value
            else None
        )
        row = existing.get(e.category_code)
        if row:
            row.relevance = e.relevance
            row.exclusion_reason = reason
            row.calculate_this_period = e.calculate_this_period
            row.data_owner = e.data_owner
            row.expected_form = e.expected_form
            row.details = e.details
            row.updated_at = now
        else:
            row = CategoryProfile(
                organization_id=current_user.organization_id,
                site_id=data.site_id,
                scope=cat["scope"],
                category_code=e.category_code,
                relevance=e.relevance,
                exclusion_reason=reason,
                calculate_this_period=e.calculate_this_period,
                data_owner=e.data_owner,
                expected_form=e.expected_form,
                details=e.details,
            )
            session.add(row)
        saved.append(row)

    await session.commit()
    for row in saved:
        await session.refresh(row)
    return [_entry_response(row) for row in saved]


# ============================================================================
# Overview (the matrix)
# ============================================================================


@router.get("/hub/overview", response_model=HubOverview)
async def hub_overview(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    period_id: UUID | None = None,
    site_id: UUID | None = None,
):
    """Every category with its profile + live coverage + open-question count.

    Coverage is org-wide (staged rows aren't site-attributed yet); site_id
    only selects which profile layer is shown.
    """
    org_id = current_user.organization_id
    profiles = await _load_profiles(session, org_id, site_id)

    # Committed reality: activities (+ their calculated emissions) per category
    act_filters = [Activity.organization_id == org_id]
    if period_id:
        act_filters.append(Activity.reporting_period_id == period_id)
    committed_rows = (
        await session.execute(
            select(
                Activity.category_code,
                func.count(Activity.id),
                func.coalesce(func.sum(Emission.co2e_kg), 0),
            )
            .outerjoin(Emission, Emission.activity_id == Activity.id)
            .where(*act_filters)
            .group_by(Activity.category_code)
        )
    ).all()

    # Staged reality: rows still in the funnel (committed ones already became
    # activities; rejected ones are discarded)
    staged_filters = [
        IngestionSession.organization_id == org_id,
        StagedRow.status.notin_([RowStatus.COMMITTED.value, RowStatus.REJECTED.value]),
    ]
    if period_id:
        staged_filters.append(IngestionSession.reporting_period_id == period_id)
    staged_rows = (
        await session.execute(
            select(
                StagedRow.category_code,
                StagedRow.measurement_tier,
                func.count(StagedRow.id),
            )
            .join(IngestionSession, StagedRow.session_id == IngestionSession.id)
            .where(*staged_filters)
            .group_by(StagedRow.category_code, StagedRow.measurement_tier)
        )
    ).all()

    # Open questions pooled per category (older questions have no category of
    # their own — fall back to their representative staged row's category)
    question_filters = [
        IngestionSession.organization_id == org_id,
        ClarificationQuestion.answered == False,  # noqa: E712
    ]
    if period_id:
        question_filters.append(IngestionSession.reporting_period_id == period_id)
    question_rows = (
        await session.execute(
            select(
                func.coalesce(
                    ClarificationQuestion.category_code, StagedRow.category_code
                ),
                func.count(ClarificationQuestion.id),
            )
            .join(
                IngestionSession,
                ClarificationQuestion.session_id == IngestionSession.id,
            )
            .outerjoin(StagedRow, ClarificationQuestion.staged_row_id == StagedRow.id)
            .where(*question_filters)
            .group_by(
                func.coalesce(
                    ClarificationQuestion.category_code, StagedRow.category_code
                )
            )
        )
    ).all()

    coverage: dict[str, CategoryCoverage] = {
        c["code"]: CategoryCoverage(staged_by_tier=dict.fromkeys(MEASUREMENT_TIERS, 0))
        for c in GHG_CATEGORIES
    }

    def hub_code(raw: str | None) -> str | None:
        if not raw:
            return None
        return HUB_CODE_FOR.get(raw)

    for code, count, co2e in committed_rows:
        target = hub_code(code)
        if target:
            coverage[target].committed_count += count
            coverage[target].total_co2e_kg += float(co2e or 0)
    for code, tier, count in staged_rows:
        target = hub_code(code)
        if target:
            coverage[target].staged_count += count
            if tier in coverage[target].staged_by_tier:
                coverage[target].staged_by_tier[tier] += count
    for code, count in question_rows:
        target = hub_code(code)
        if target:
            coverage[target].open_questions += count

    categories: list[HubCategory] = []
    stats = HubStats(
        total_categories=len(GHG_CATEGORIES),
        relevant=0,
        not_relevant=0,
        not_sure=0,
        with_data=0,
        open_questions=0,
    )
    for cat in GHG_CATEGORIES:
        profile = profiles.get(cat["code"])
        cov = coverage[cat["code"]]
        relevance = (
            (
                profile.relevance.value
                if isinstance(profile.relevance, CategoryRelevance)
                else profile.relevance
            )
            if profile
            else CategoryRelevance.NOT_SURE.value
        )
        if relevance == CategoryRelevance.RELEVANT.value:
            stats.relevant += 1
            if cov.committed_count or cov.staged_count:
                stats.with_data += 1
        elif relevance == CategoryRelevance.NOT_RELEVANT.value:
            stats.not_relevant += 1
        else:
            stats.not_sure += 1
        stats.open_questions += cov.open_questions
        categories.append(
            HubCategory(
                scope=cat["scope"],
                code=cat["code"],
                name=cat["name"],
                description=cat["description"],
                profile=_entry_response(profile) if profile else None,
                coverage=cov,
            )
        )

    return HubOverview(categories=categories, stats=stats)
