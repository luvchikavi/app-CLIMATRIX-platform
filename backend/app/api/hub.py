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
from app.services.methodology import tier_of_score
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


class HubQuestion(BaseModel):
    """An open clarifying question, pooled per category for the drawer."""

    id: str
    session_id: str
    filename: str
    question: str
    field: str | None = None
    choices: list | None = None
    applies_count: int = 1


@router.get("/hub/questions", response_model=list[HubQuestion])
async def hub_questions(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    category_code: str,
    period_id: UUID | None = None,
):
    """Open questions for one hub category, across every upload session."""
    codes = CATEGORY_BY_CODE.get(category_code, {}).get("aggregates", [category_code])
    filters = [
        IngestionSession.organization_id == current_user.organization_id,
        ClarificationQuestion.answered == False,  # noqa: E712
        func.coalesce(ClarificationQuestion.category_code, StagedRow.category_code).in_(
            codes
        ),
    ]
    if period_id:
        filters.append(IngestionSession.reporting_period_id == period_id)
    rows = (
        await session.execute(
            select(ClarificationQuestion, IngestionSession.filename)
            .join(
                IngestionSession,
                ClarificationQuestion.session_id == IngestionSession.id,
            )
            .outerjoin(StagedRow, ClarificationQuestion.staged_row_id == StagedRow.id)
            .where(*filters)
            .order_by(ClarificationQuestion.created_at.desc())
            .limit(50)
        )
    ).all()
    return [
        HubQuestion(
            id=str(q.id),
            session_id=str(q.session_id),
            filename=filename,
            question=q.question,
            field=q.field,
            choices=q.choices,
            applies_count=len(q.applies_to_row_ids or []) or 1,
        )
        for q, filename in rows
    ]


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


# ============================================================================
# Punch-list — the verification export (§5 of the spec)
# ============================================================================


# Canonical PCAF-score → ladder-tier mapping lives in the methodology module
# so hub, reports, and parser can never drift apart.
_tier_of_score = tier_of_score


@router.get("/hub/punch-list")
async def punch_list(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    period_id: UUID | None = None,
    format: str = "json",
):
    """The auditor-facing punch-list: per category, what's solid, what's an
    estimate (and what would upgrade it), what's a documented exclusion, and
    what's still missing entirely — with the concrete next action for each."""
    from datetime import timezone

    from fastapi.responses import PlainTextResponse

    from app.models.core import Organization, ReportingPeriod
    from app.services.entitlements import (
        ensure_period_year_licensed,
        get_entitlement,
        require_report_generation,
    )

    entitlement = None
    if format == "csv":
        # The CSV download is an export — same teaser rule as report exports.
        entitlement = await get_entitlement(current_user, session)
        await require_report_generation(entitlement)

    org_id = current_user.organization_id
    org = await session.get(Organization, org_id)
    period = await session.get(ReportingPeriod, period_id) if period_id else None
    if period and period.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Reporting period not found")
    if entitlement is not None:
        # Report Pass: the CSV export is licensed to the pass's reporting year.
        ensure_period_year_licensed(entitlement, period)

    profiles = await _load_profiles(session, org_id, None)

    act_filters = [Activity.organization_id == org_id]
    if period_id:
        act_filters.append(Activity.reporting_period_id == period_id)
    committed = (
        await session.execute(
            select(
                Activity.category_code,
                Activity.data_quality_score,
                func.count(Activity.id),
                func.coalesce(func.sum(Emission.co2e_kg), 0),
            )
            .outerjoin(Emission, Emission.activity_id == Activity.id)
            .where(*act_filters)
            .group_by(Activity.category_code, Activity.data_quality_score)
        )
    ).all()

    q_filters = [
        IngestionSession.organization_id == org_id,
        ClarificationQuestion.answered == False,  # noqa: E712
    ]
    if period_id:
        q_filters.append(IngestionSession.reporting_period_id == period_id)
    open_qs = (
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
            .where(*q_filters)
            .group_by(
                func.coalesce(
                    ClarificationQuestion.category_code, StagedRow.category_code
                )
            )
        )
    ).all()

    per_cat: dict[str, dict] = {
        c["code"]: {
            "count": 0,
            "co2e_kg": 0.0,
            "tiers": {"measured": 0.0, "calculated": 0.0, "estimated": 0.0},
            "questions": 0,
        }
        for c in GHG_CATEGORIES
    }
    for code, score, count, co2e in committed:
        hub = HUB_CODE_FOR.get(code)
        if not hub:
            continue
        entry = per_cat[hub]
        entry["count"] += count
        entry["co2e_kg"] += float(co2e or 0)
        entry["tiers"][_tier_of_score(score)] += float(co2e or 0)
    for code, count in open_qs:
        hub = HUB_CODE_FOR.get(code or "")
        if hub:
            per_cat[hub]["questions"] += count

    total_co2e = sum(e["co2e_kg"] for e in per_cat.values())
    solid_co2e = sum(
        e["tiers"]["measured"] + e["tiers"]["calculated"] for e in per_cat.values()
    )

    categories = []
    actions = []
    for cat in GHG_CATEGORIES:
        p = profiles.get(cat["code"])
        relevance = (
            (p.relevance if isinstance(p.relevance, str) else p.relevance.value)
            if p
            else "not_sure"
        )
        e = per_cat[cat["code"]]
        owner = p.data_owner if p else None
        ask = f" — ask {owner}" if owner else ""

        if relevance == "not_relevant":
            verdict, action = "excluded", (
                f"Documented exclusion: {p.exclusion_reason or 'no reason recorded'}"
            )
            if not (p and p.exclusion_reason):
                actions.append(
                    f"{cat['code']} {cat['name']}: excluded WITHOUT a reason — record one."
                )
        elif relevance == "not_sure":
            verdict, action = "undecided", "Decide: is this category relevant?"
            actions.append(
                f"{cat['code']} {cat['name']}: still undecided — settle relevance."
            )
        elif e["count"] == 0:
            verdict, action = "gap", f"No data at all{ask}."
            actions.append(f"{cat['code']} {cat['name']}: GAP — no data{ask}.")
        elif e["tiers"]["estimated"] > 0.5 * max(e["co2e_kg"], 1e-9):
            verdict = "estimated"
            action = (
                "Mostly spend/proxy-based — request physical quantities "
                f"(meter readings, invoices with amounts){ask} to upgrade."
            )
            actions.append(
                f"{cat['code']} {cat['name']}: {e['tiers']['estimated'] / 1000:,.1f} t "
                f"is estimate-based — physical data would upgrade it{ask}."
            )
        else:
            verdict, action = "solid", "Measured/calculated basis — stands as reported."
        if e["questions"]:
            actions.append(
                f"{cat['code']} {cat['name']}: {e['questions']} open question(s) blocking rows."
            )
        categories.append(
            {
                "code": cat["code"],
                "name": cat["name"],
                "scope": cat["scope"],
                "relevance": relevance,
                "verdict": verdict,
                "action": action,
                "data_owner": owner,
                "activity_count": e["count"],
                "co2e_kg": round(e["co2e_kg"], 1),
                "co2e_by_tier_kg": {k: round(v, 1) for k, v in e["tiers"].items()},
                "open_questions": e["questions"],
            }
        )

    result = {
        "organization": {
            "name": org.name if org else "",
            "country_code": org.country_code if org else None,
            "consolidation_approach": (
                org.consolidation_approach if org else "operational_control"
            ),
            "currency": org.currency if org else None,
        },
        "period": {
            "name": period.name if period else "all periods",
            "start_date": str(period.start_date) if period else None,
            "end_date": str(period.end_date) if period else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "co2e_kg": round(total_co2e, 1),
            "solid_co2e_kg": round(solid_co2e, 1),
            "solid_share": round(solid_co2e / total_co2e, 3) if total_co2e else None,
        },
        "categories": categories,
        "punch_list": actions,
    }

    if format == "csv":
        lines = ["code,name,scope,relevance,verdict,co2e_kg,open_questions,action"]
        for c in categories:
            action_text = c["action"].replace('"', "'")
            lines.append(
                f"{c['code']},\"{c['name']}\",{c['scope']},{c['relevance']},"
                f"{c['verdict']},{c['co2e_kg']},{c['open_questions']},\"{action_text}\""
            )
        return PlainTextResponse(
            "\n".join(lines),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=climatrix-punch-list.csv"
            },
        )
    return result
