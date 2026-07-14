"""Sample data: seed and remove the Galil Steel demo dataset for an org.

"Load sample data" gives an empty org a fully populated product in one click:
a demo site + reporting period, 51 activities calculated through the real
CalculationPipeline, and an SBTi target with two scenarios built from the
org's own recommendation engine output (same logic as the conference seed
script). Every row is flagged is_demo=True; remove() deletes exactly that
set and nothing else, so a user's real data is never touched.
"""

import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.data.sample_dataset import (
    SAMPLE_ACHIEVEMENT_CAP,
    SAMPLE_ACTIVITIES,
    SAMPLE_BASE_YEAR,
    SAMPLE_DATA_QUALITY_SCORE,
    SAMPLE_PERIOD,
    SAMPLE_REGION,
    SAMPLE_SCENARIO_1,
    SAMPLE_SCENARIO_2,
    SAMPLE_SITE,
    SAMPLE_TARGET_DESCRIPTION,
    SAMPLE_TARGET_NAME,
    SAMPLE_TARGET_YEAR,
)
from app.models.cbam import CBAMImport
from app.models.core import Organization, ReportingPeriod, Site, User
from app.models.decarbonization import (
    DecarbonizationTarget,
    EmissionCheckpoint,
    RoadmapMilestone,
    Scenario,
    ScenarioInitiative,
    ScenarioType,
    TargetFramework,
    TargetType,
)
from app.models.emission import Activity, ConfidenceLevel, Emission, ImportBatch
from app.models.hub import CategoryProfile
from app.models.ingestion import IngestionSession
from app.services.calculation import ActivityInput, CalculationPipeline
from app.services.calculation.pipeline import CalculationError
from app.services.calculation.normalizer import UnitConversionError
from app.services.calculation.resolver import FactorNotFoundError
from app.services.decarbonization import (
    EmissionProfileService,
    RecommendationEngine,
    ScenarioService,
    TargetCalculationService,
)

logger = logging.getLogger(__name__)

# Staggered implementation windows for the flagship scenario's initiatives
_SCENARIO_1_WINDOWS = [
    (date(2026, 1, 1), date(2027, 6, 30)),
    (date(2026, 7, 1), date(2027, 12, 31)),
    (date(2027, 1, 1), date(2028, 12, 31)),
    (date(2027, 7, 1), date(2029, 6, 30)),
]
_SCENARIO_2_ENDS = [date(2026, 12, 31), date(2027, 6, 30), date(2027, 12, 31)]


class SampleDataAlreadyLoaded(Exception):
    """The org already has sample data — load() refuses to double-seed."""


class SampleDataService:
    """Seed / inspect / remove the flagged sample dataset for one org."""

    @staticmethod
    async def status(session: AsyncSession, organization_id: UUID) -> dict:
        activities = (
            await session.execute(
                select(func.count())
                .select_from(Activity)
                .where(
                    Activity.organization_id == organization_id,
                    Activity.is_demo == True,  # noqa: E712
                )
            )
        ).scalar_one()

        period_id = (
            await session.execute(
                select(ReportingPeriod.id)
                .where(
                    ReportingPeriod.organization_id == organization_id,
                    ReportingPeriod.is_demo == True,  # noqa: E712
                )
                .limit(1)
            )
        ).scalar_one_or_none()

        return {
            "loaded": activities > 0,
            "period_id": str(period_id) if period_id else None,
            "activities": activities,
        }

    @staticmethod
    async def load(session: AsyncSession, user: User) -> dict:
        org = await session.get(Organization, user.organization_id)
        if org is None:
            raise ValueError("Organization not found")

        existing = await SampleDataService.status(session, org.id)
        if existing["loaded"]:
            raise SampleDataAlreadyLoaded()

        site = Site(organization_id=org.id, is_demo=True, **SAMPLE_SITE)
        period = ReportingPeriod(organization_id=org.id, is_demo=True, **SAMPLE_PERIOD)
        session.add(site)
        session.add(period)
        await session.flush()

        pipeline = CalculationPipeline(session)
        created = 0
        skipped: list[str] = []
        total_co2e_kg = Decimal("0")

        for row in SAMPLE_ACTIVITIES:
            try:
                calc = await pipeline.calculate(
                    ActivityInput(
                        activity_key=row["activity_key"],
                        quantity=Decimal(str(row["quantity"])),
                        unit=row["unit"],
                        scope=row["scope"],
                        category_code=row["category_code"],
                        region=SAMPLE_REGION,
                        year=SAMPLE_BASE_YEAR,
                    )
                )
            except (FactorNotFoundError, UnitConversionError, CalculationError) as exc:
                skipped.append(f"{row['activity_key']} ({row['activity_date']}): {exc}")
                continue

            activity = Activity(
                organization_id=org.id,
                reporting_period_id=period.id,
                site_id=site.id,
                scope=row["scope"],
                category_code=row["category_code"],
                activity_key=row["activity_key"],
                description=row["description"],
                quantity=Decimal(str(row["quantity"])),
                unit=row["unit"],
                activity_date=row["activity_date"],
                data_quality_score=SAMPLE_DATA_QUALITY_SCORE,
                created_by=user.id,
                is_demo=True,
            )
            session.add(activity)
            await session.flush()

            session.add(
                Emission(
                    activity_id=activity.id,
                    emission_factor_id=calc.emission_factor_id,
                    co2e_kg=calc.co2e_kg,
                    co2_kg=calc.co2_kg,
                    ch4_kg=calc.ch4_kg,
                    n2o_kg=calc.n2o_kg,
                    wtt_co2e_kg=calc.wtt_co2e_kg,
                    converted_quantity=calc.converted_quantity,
                    converted_unit=calc.converted_unit,
                    formula=calc.formula,
                    confidence=ConfidenceLevel(calc.confidence),
                    resolution_strategy=calc.resolution_strategy,
                    factor_year=calc.factor_year,
                    factor_region=calc.factor_region,
                    method_hierarchy=calc.method_hierarchy,
                    location_co2e_kg=calc.location_co2e_kg,
                    market_co2e_kg=calc.market_co2e_kg,
                )
            )
            created += 1
            total_co2e_kg += calc.co2e_kg

        if skipped:
            logger.warning("Sample data: %d rows skipped: %s", len(skipped), skipped)

        target_created = False
        scenarios_created = 0
        if created:
            try:
                scenarios_created, target_created = (
                    await SampleDataService._seed_decarbonization(
                        session, org.id, user.id, period.id
                    )
                )
            except Exception:
                # The dashboard/report part of the sample must still land even
                # if the initiative library or profile analysis is unavailable.
                logger.exception("Sample data: decarbonization seeding failed")

        await session.commit()

        return {
            "period_id": str(period.id),
            "site_id": str(site.id),
            "activities_created": created,
            "rows_skipped": len(skipped),
            "total_co2e_tonnes": float(round(total_co2e_kg / 1000, 1)),
            "target_created": target_created,
            "scenarios_created": scenarios_created,
        }

    @staticmethod
    async def _seed_decarbonization(
        session: AsyncSession, organization_id: UUID, user_id: UUID, period_id: UUID
    ) -> tuple[int, bool]:
        """SBTi target + two scenarios from the org's own recommendations.

        Mirrors qa-conference/seed_scenarios.py: one initiative per emission
        source (stacking measures on the same source double-counts), flagship
        scenario trimmed to ~112% target achievement.
        """
        recommendations = await RecommendationEngine.generate_recommendations(
            session=session,
            organization_id=organization_id,
            period_id=period_id,
            limit=20,
        )
        if not recommendations:
            return 0, False

        # Base-year emissions as the profile analysis sees them, so the
        # target and the recommendations tell one consistent story.
        profile = await EmissionProfileService.analyze_period(
            session, organization_id, period_id
        )
        base_emissions = round(profile.total_co2e_tonnes, 1)
        if base_emissions <= 0:
            return 0, False

        target_emissions, reduction_pct = (
            TargetCalculationService.calculate_target_emissions(
                base_year_emissions=base_emissions,
                base_year=SAMPLE_BASE_YEAR,
                target_year=SAMPLE_TARGET_YEAR,
                framework=TargetFramework.SBTI_1_5C,
            )
        )
        target = DecarbonizationTarget(
            organization_id=organization_id,
            name=SAMPLE_TARGET_NAME,
            description=SAMPLE_TARGET_DESCRIPTION,
            target_type=TargetType.ABSOLUTE,
            framework=TargetFramework.SBTI_1_5C,
            base_year=SAMPLE_BASE_YEAR,
            base_year_period_id=period_id,
            base_year_emissions_tco2e=base_emissions,
            target_year=SAMPLE_TARGET_YEAR,
            target_reduction_percent=reduction_pct,
            target_emissions_tco2e=target_emissions,
            created_by_id=user_id,
            is_demo=True,
        )
        session.add(target)
        await session.flush()

        # Scenario 1 — biggest reduction per distinct emission source
        by_impact: list = []
        seen_sources: set[str] = set()
        for rec in sorted(
            recommendations, key=lambda r: r.potential_reduction_tco2e, reverse=True
        ):
            if rec.target_activity_key in seen_sources:
                continue
            seen_sources.add(rec.target_activity_key)
            by_impact.append(rec)
            if len(by_impact) == 4:
                break

        required_reduction = base_emissions - target_emissions
        picks = SampleDataService._trim_to_cap(by_impact, required_reduction)

        scenario_1 = Scenario(
            organization_id=organization_id,
            target_id=target.id,
            scenario_type=ScenarioType(SAMPLE_SCENARIO_1["scenario_type"]),
            name=SAMPLE_SCENARIO_1["name"],
            description=SAMPLE_SCENARIO_1["description"],
            carbon_price_scenario="moderate",
            is_active=True,
            created_by_id=user_id,
            is_demo=True,
        )
        session.add(scenario_1)
        await session.flush()

        for i, (rec, reduction, scale) in enumerate(picks):
            start, end = _SCENARIO_1_WINDOWS[i % len(_SCENARIO_1_WINDOWS)]
            note = None
            if scale < 1:
                note = (
                    f"Phased rollout — this scenario deploys ~{round(scale * 100)}% "
                    "of the measure's technical potential."
                )
            session.add(
                SampleDataService._build_initiative(
                    scenario_1.id, rec, reduction, scale, start, end, i, note
                )
            )
        await session.flush()
        await ScenarioService.update_scenario_metrics(session, scenario_1.id)

        # Scenario 2 — quick wins: highest feasibility, sources/initiatives
        # not already used, no scaling (small numbers read honestly)
        used_initiatives = {rec.initiative_id for rec, _, _ in picks}
        quick: list = []
        q_sources: set[str] = set()
        for rec in sorted(
            recommendations,
            key=lambda r: (-r.feasibility_score, float(r.estimated_capex or 0)),
        ):
            if (
                rec.initiative_id in used_initiatives
                or rec.initiative_id in {q.initiative_id for q in quick}
                or rec.target_activity_key in q_sources
            ):
                continue
            q_sources.add(rec.target_activity_key)
            quick.append(rec)
            if len(quick) == 3:
                break
        if not quick:  # small library — allow overlap over an empty scenario
            quick = sorted(recommendations, key=lambda r: -r.feasibility_score)[:2]

        scenario_2 = Scenario(
            organization_id=organization_id,
            target_id=target.id,
            scenario_type=ScenarioType(SAMPLE_SCENARIO_2["scenario_type"]),
            name=SAMPLE_SCENARIO_2["name"],
            description=SAMPLE_SCENARIO_2["description"],
            carbon_price_scenario="moderate",
            is_active=False,
            created_by_id=user_id,
            is_demo=True,
        )
        session.add(scenario_2)
        await session.flush()

        for i, rec in enumerate(quick):
            session.add(
                SampleDataService._build_initiative(
                    scenario_2.id,
                    rec,
                    rec.potential_reduction_tco2e,
                    Decimal("1"),
                    date(2026, 1, 1),
                    _SCENARIO_2_ENDS[i % len(_SCENARIO_2_ENDS)],
                    i,
                    None,
                )
            )
        await session.flush()
        await ScenarioService.update_scenario_metrics(session, scenario_2.id)

        return 2, True

    @staticmethod
    def _trim_to_cap(recs: list, required_reduction: Decimal) -> list[tuple]:
        """Scale the largest picks down until total reduction sits near the
        achievement cap (~112% of the target), so the flagship scenario tells
        a credible story instead of stacking full technical potential.

        Returns [(recommendation, reduction_tco2e, scale)].
        """
        picks = [(rec, Decimal(rec.potential_reduction_tco2e)) for rec in recs]
        cap_total = required_reduction * Decimal(str(SAMPLE_ACHIEVEMENT_CAP))
        total = sum(r for _, r in picks)

        result = []
        for rec, reduction in sorted(picks, key=lambda p: p[1], reverse=True):
            excess = total - cap_total
            if excess > 0:
                floor = reduction * Decimal("0.2")  # keep the measure meaningful
                trimmed = max(floor, reduction - excess)
                total -= reduction - trimmed
                scale = (
                    (trimmed / reduction).quantize(Decimal("0.01"))
                    if reduction
                    else Decimal("1")
                )
                result.append((rec, round(trimmed, 1), scale))
            else:
                result.append((rec, round(reduction, 1), Decimal("1")))
        return result

    @staticmethod
    def _build_initiative(
        scenario_id: UUID,
        rec,
        reduction: Decimal,
        scale: Decimal,
        start: date,
        end: date,
        priority: int,
        note: str | None,
    ) -> ScenarioInitiative:
        source = Decimal(rec.target_source_emissions_tco2e) or Decimal("1")
        return ScenarioInitiative(
            scenario_id=scenario_id,
            initiative_id=rec.initiative_id,
            target_activity_key=rec.target_activity_key,
            expected_reduction_tco2e=reduction,
            expected_reduction_percent=min(
                Decimal("100"), round(reduction / source * 100, 1)
            ),
            capex=round(Decimal(rec.estimated_capex or 0) * scale, 0),
            annual_savings=round(Decimal(rec.estimated_annual_savings or 0) * scale, 0),
            implementation_start=start,
            implementation_end=end,
            priority_order=priority,
            notes=note,
        )

    @staticmethod
    async def remove(session: AsyncSession, organization_id: UUID) -> dict:
        """Delete everything is_demo for this org, FK-safe order.

        The demo period/site are kept (flag cleared) if the user has attached
        their own data to them in the meantime.
        """

        async def _ids(stmt) -> list[UUID]:
            return list((await session.execute(stmt)).scalars().all())

        async def _count(model, *where) -> int:
            return (
                await session.execute(
                    select(func.count()).select_from(model).where(*where)
                )
            ).scalar_one()

        scenario_ids = await _ids(
            select(Scenario.id).where(
                Scenario.organization_id == organization_id,
                Scenario.is_demo == True,  # noqa: E712
            )
        )
        if scenario_ids:
            await session.execute(
                delete(ScenarioInitiative).where(
                    ScenarioInitiative.scenario_id.in_(scenario_ids)
                )
            )
            await session.execute(
                delete(RoadmapMilestone).where(
                    RoadmapMilestone.scenario_id.in_(scenario_ids)
                )
            )
            await session.execute(delete(Scenario).where(Scenario.id.in_(scenario_ids)))

        target_ids = await _ids(
            select(DecarbonizationTarget.id).where(
                DecarbonizationTarget.organization_id == organization_id,
                DecarbonizationTarget.is_demo == True,  # noqa: E712
            )
        )
        if target_ids:
            await session.execute(
                delete(EmissionCheckpoint).where(
                    EmissionCheckpoint.target_id.in_(target_ids)
                )
            )
            await session.execute(
                delete(DecarbonizationTarget).where(
                    DecarbonizationTarget.id.in_(target_ids)
                )
            )

        activity_ids = await _ids(
            select(Activity.id).where(
                Activity.organization_id == organization_id,
                Activity.is_demo == True,  # noqa: E712
            )
        )
        if activity_ids:
            await session.execute(
                delete(Emission).where(Emission.activity_id.in_(activity_ids))
            )
            await session.execute(delete(Activity).where(Activity.id.in_(activity_ids)))

        periods_removed = 0
        periods_kept = 0
        demo_periods = (
            (
                await session.execute(
                    select(ReportingPeriod).where(
                        ReportingPeriod.organization_id == organization_id,
                        ReportingPeriod.is_demo == True,  # noqa: E712
                    )
                )
            )
            .scalars()
            .all()
        )
        for period in demo_periods:
            refs = (
                await _count(Activity, Activity.reporting_period_id == period.id)
                + await _count(
                    ImportBatch, ImportBatch.reporting_period_id == period.id
                )
                + await _count(
                    IngestionSession, IngestionSession.reporting_period_id == period.id
                )
                + await _count(CBAMImport, CBAMImport.reporting_period_id == period.id)
                + await _count(
                    DecarbonizationTarget,
                    DecarbonizationTarget.base_year_period_id == period.id,
                )
                + await _count(
                    EmissionCheckpoint,
                    EmissionCheckpoint.reporting_period_id == period.id,
                )
            )
            if refs == 0:
                await session.delete(period)
                periods_removed += 1
            else:
                period.is_demo = False  # user data lives here now — keep it as theirs
                session.add(period)
                periods_kept += 1

        demo_sites = (
            (
                await session.execute(
                    select(Site).where(
                        Site.organization_id == organization_id,
                        Site.is_demo == True,  # noqa: E712
                    )
                )
            )
            .scalars()
            .all()
        )
        for site in demo_sites:
            refs = (
                await _count(Activity, Activity.site_id == site.id)
                + await _count(
                    ScenarioInitiative, ScenarioInitiative.target_site_id == site.id
                )
                + await _count(CategoryProfile, CategoryProfile.site_id == site.id)
            )
            if refs == 0:
                await session.delete(site)
            else:
                site.is_demo = False
                session.add(site)

        await session.commit()

        return {
            "removed_activities": len(activity_ids),
            "removed_scenarios": len(scenario_ids),
            "removed_targets": len(target_ids),
            "period_removed": periods_removed > 0,
            "periods_kept": periods_kept,
        }
