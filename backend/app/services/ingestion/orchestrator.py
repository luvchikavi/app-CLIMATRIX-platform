"""Ingestion orchestrator — drives one uploaded file end to end.

This is the conductor that turns a raw upload into reviewable, committable rows:

  load → sanitise → map (LLM) → ground → rule-check → score → stage
       → collect clarifying questions → (client answers) → re-score
       → commit approved rows through the real CalculationPipeline

Every source row lands as a :class:`StagedRow`; anything the parser is unsure about
becomes a :class:`ClarificationQuestion`. Nothing hits the emissions ledger until
:func:`commit_session`, which runs each confirmed row through the same pipeline the
rest of the app uses — so imported numbers are identical to hand-entered ones.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Organization, ReportingPeriod, Site
from app.models.emission import (
    Activity,
    DataSource,
    Emission,
    ConfidenceLevel,
    ImportBatch,
    ImportBatchStatus,
)
from app.models.hub import (
    CATEGORY_BY_CODE,
    HUB_CODE_FOR,
    CategoryProfile,
    CategoryRelevance,
)
from app.models.ingestion import (
    ClarificationQuestion,
    IngestionSession,
    IngestionStatus,
    RowStatus,
    StagedRow,
)
from app.services.calculation import CalculationPipeline, ActivityInput
from app.services.calculation.pipeline import CalculationError
from app.services.calculation.resolver import FactorNotFoundError, base_factor_region
from app.services.calculation.normalizer import UnitConversionError
from app.services.ingestion import catalog as catalog_mod
from app.services.ingestion.confidence import score_row
from app.services.ingestion.file_guard import sanitise_rows, scan_text_for_injection
from app.services.ingestion.grounding import (
    GroundingVerdict,
    ground_row,
    classify_unit,
)
from app.services.ingestion.context import build_parsing_context
from app.services.ingestion.derivation import (
    apply_derivation_answer,
    apply_derivation_to_mapped,
    derive_for_rows,
    stamp_derived_verdict,
)
from app.services.ingestion.plausibility import check_batch
from app.services.ingestion.loader import load_with_skipped
from app.services.ingestion.mapper import map_table
from app.services.ingestion.fast_mapper import map_table_fast
from app.services.ingestion.rule_engine import check_row
from app.services.ingestion.template_bridge import detect_template, map_template

# Statuses that a commit will actually write to the ledger.
_COMMITTABLE = {RowStatus.READY, RowStatus.APPROVED}

# How many sheets to map concurrently. The fast mapper is only ~2 LLM calls/sheet,
# so we can run many sheets at once (a 26-sheet file finishes in a couple of waves).
_MAP_CONCURRENCY = 10


async def annotate_duplicate(
    session: AsyncSession, ingestion: IngestionSession
) -> None:
    """Flag (non-blocking) when this exact file was already committed for the org.

    Shared by the inline and worker analysis paths so re-importing the same bytes
    always warns about double-counting, regardless of how parsing was dispatched.
    """
    if not ingestion.content_hash:
        return
    duplicate_of = (
        (
            await session.execute(
                select(IngestionSession.id)
                .where(
                    IngestionSession.organization_id == ingestion.organization_id,
                    IngestionSession.content_hash == ingestion.content_hash,
                    IngestionSession.status == IngestionStatus.COMMITTED.value,
                    IngestionSession.id != ingestion.id,
                )
                .limit(1)
            )
        )
        .scalars()
        .first()
    )
    if duplicate_of is None:
        return
    summary = dict(ingestion.summary or {})
    summary["duplicate_warning"] = (
        "This exact file was already imported and committed for your organization. "
        "Committing again will double-count these emissions."
    )
    summary["duplicate_of"] = str(duplicate_of)
    ingestion.summary = summary


_METHOD_LABEL = {
    "exact": "Activity data × specific factor",
    "region": "Activity data × regional factor",
    "supplier": "Supplier-specific factor",
    "defra_physical": "Activity data × DEFRA factor",
    "ecoinvent": "Activity data × ecoinvent factor",
    "global": "Activity data × global-average factor",
    "eeio_spend": "Spend-based (EEIO) estimate",
    "not_found": "No factor found",
}


def _provenance(grounding: GroundingVerdict, unit: str | None) -> dict:
    """The full 'story' of a line for review + audit: which factor, from where, how."""
    return {
        "factor_source": grounding.factor_source,
        "factor_year": grounding.factor_year,
        "factor_region": grounding.factor_region,
        "factor_name": grounding.factor_name,
        "method": grounding.strategy,
        "method_label": _METHOD_LABEL.get(grounding.strategy, grounding.strategy),
        "unit_kind": classify_unit(unit) if unit else None,
    }


def _resolve_year(year: int | None) -> tuple[int, bool]:
    """Factor vintage to ground against.

    When the caller has no reporting period (ingest without a period selected)
    we fall back to the CURRENT year — never a hardcoded past vintage — and
    report the assumption so affected rows can carry an audit-trail reason.
    Returns ``(year, was_assumed)``.
    """
    if year is not None:
        return year, False
    return datetime.utcnow().year, True


def _year_assumed_reason(year: int) -> str:
    return (
        f"No reporting period selected — assumed factor year {year} "
        f"(current year). Select a period to pin the factor vintage."
    )


def _no_key_verdict(reason: str) -> GroundingVerdict:
    """Grounding verdict for a row the mapper could not confidently map to a key."""
    return GroundingVerdict(
        resolved=False,
        strategy="not_found",
        factor_unit=None,
        unit_ok=False,
        needs_question=True,
        confidence_cap=0.0,
        pcaf_data_quality=5,
        reason=reason,
    )


async def run_analysis(
    session: AsyncSession,
    ingestion: IngestionSession,
    content: bytes,
    filename: str,
    *,
    client=None,
    region: str = "Global",
    year: int | None = None,
) -> IngestionSession:
    """Parse an upload into staged rows + clarifying questions.

    Deterministic apart from the single LLM mapping call per sheet. On any
    unexpected failure the session is marked FAILED with a client-safe message
    rather than left half-done.
    """
    year, year_assumed = _resolve_year(year)
    ingestion.status = IngestionStatus.ANALYZING
    ingestion.updated_at = datetime.utcnow()
    await session.flush()

    cat = await catalog_mod.build_from_db(session)

    # Everything the org already declared (hub profile, currency, units, sites)
    # rides along on every parse — the LLM never guesses what the client answered.
    context = await build_parsing_context(
        session, ingestion.organization_id, ingestion.reporting_period_id
    )

    # FAST PATH — our own template. Known sheets, exact semantics: parse
    # deterministically (no LLM), stage directly. Foreign files fall through.
    template_results = None
    if detect_template(content, filename):
        template_results = await asyncio.to_thread(map_template, content, filename)

    parse_mode = "template" if template_results is not None else "ai"
    skipped_sheets: list[str] = []
    if template_results is not None:
        # Template rows carry explicit quantities/units — no derivation needed.
        mapped_results = [(tbl, rows, 0, 0, None, {}) for tbl, rows in template_results]
    else:
        try:
            tables, skipped_sheets = load_with_skipped(content, filename)
        except NotImplementedError as exc:
            ingestion.status = IngestionStatus.FAILED
            ingestion.error_message = str(exc)
            await session.flush()
            return ingestion
        except Exception as exc:  # pragma: no cover - defensive
            ingestion.status = IngestionStatus.FAILED
            ingestion.error_message = f"Could not read the file: {exc}"
            await session.flush()
            return ingestion

    total = 0
    mapped = 0
    questions = 0
    by_scope: dict[str, int] = {}
    by_band = {"green": 0, "amber": 0, "red": 0}
    by_tier = {"measured": 0, "calculated": 0, "estimated": 0, "gap": 0}
    sheets_summary: list[dict] = []
    security = {"formula_cells_sanitised": 0, "injection_flags": 0}
    # Clarifying questions accumulate into GROUPS so we ask each distinct issue once
    # (all "PP" rows share one question) instead of once per row. Keyed by group_key.
    question_groups: dict[str, dict] = {}
    all_staged: list[StagedRow] = []

    if template_results is None:
        # Phase 1 — map every sheet CONCURRENTLY. The LLM calls are the slow, DB-free
        # part; a 26-sheet workbook would otherwise be 10+ sequential AI calls (minutes).
        # Grounding + staging (which touch the DB session) still run sequentially below.
        _sem = asyncio.Semaphore(_MAP_CONCURRENCY)

        async def _map_sheet(tbl):
            clean, fh, ih = sanitise_rows(tbl.rows)
            tbl.rows = clean
            async with _sem:
                try:
                    # Fast path: ~2 LLM calls/sheet (column map + distinct values).
                    mr = await asyncio.to_thread(
                        map_table_fast, tbl, cat, None, client, context
                    )
                except Exception:
                    # Fall back to the slower but battle-tested row-level mapper.
                    try:
                        mr = await asyncio.to_thread(map_table, tbl, cat, None, client)
                    except Exception as exc:  # a bad sheet shouldn't kill the file
                        return (tbl, None, fh, ih, str(exc)[:200], {})
                # Derived-quantity stage: travel/freight rows whose quantity
                # isn't usable in the factor's unit get one computed from the
                # bundled gazetteers (entities via one fast LLM call, math
                # deterministic). Failure falls back to the question flow.
                derivs = await asyncio.to_thread(derive_for_rows, mr, client, context)
                return (tbl, mr, fh, ih, None, derivs)

        mapped_results = await asyncio.gather(*[_map_sheet(t) for t in tables])

    for table, mapped_rows, formula_hits, injection_hits, err, derivs in mapped_results:
        security["formula_cells_sanitised"] += formula_hits
        security["injection_flags"] += injection_hits
        if err is not None or mapped_rows is None:
            sheets_summary.append(
                {
                    "sheet": table.sheet,
                    "rows": table.row_count,
                    "error": err or "map failed",
                }
            )
            continue

        sheet_staged = 0
        for m in mapped_rows:
            total += 1
            # Derived-quantity stage result for this row (flight km, hotel
            # nights, freight tonne-km) — applied BEFORE grounding so the row
            # grounds against a real quantity in the factor's own unit.
            deriv = derivs.get(m.row_index)
            if deriv is not None:
                apply_derivation_to_mapped(m, deriv, cat)
            if m.activity_key:
                mapped += 1
                grounding = await ground_row(
                    session,
                    m.activity_key,
                    m.unit or "",
                    # A derived row-level region (a hotel's stay country) beats
                    # the org default at review time too — the grid must show
                    # the factor that will actually be committed.
                    region=(deriv.region if deriv is not None else None) or region,
                    year=year,
                )
                violations = check_row(
                    cat, m.activity_key, m.scope or 0, m.category_code or ""
                )
            else:
                grounding = _no_key_verdict(
                    "Couldn't confidently match this to an activity type — please confirm."
                )
                violations = []

            verdict = score_row(grounding, violations, llm_self_score=m.llm_confidence)

            # A derived quantity is honest but ESTIMATED — floor PCAF at 4 and
            # put every assumption (route, ×2, defaults, upgrade path) on the
            # row's audit trail.
            if deriv is not None:
                stamp_derived_verdict(verdict, deriv)

            # Grounded against an assumed (current-year) factor vintage because no
            # reporting period was selected — say so on the row's audit trail.
            if year_assumed and m.activity_key:
                verdict.reasons.append(_year_assumed_reason(year))

            # Prompt-injection in the row text: never trust it silently.
            row_text = (
                f"{m.description} {' '.join(str(v) for v in (m.source or {}).values())}"
            )
            if scan_text_for_injection(row_text):
                verdict.reasons.append(
                    "Contains instruction-like text — flagged for manual review (possible injection)."
                )
                if verdict.status == RowStatus.READY.value:
                    verdict.status = "needs_review"

            prov = _provenance(grounding, m.unit)
            if deriv is not None:
                # Full derivation state → provenance, so the number is
                # reproducible end-to-end and answers can recompute it.
                prov["derivation"] = deriv.state
            staged = StagedRow(
                session_id=ingestion.id,
                sheet=table.sheet,
                row_index=m.row_index,
                source=_json_safe_dict(m.source),
                activity_key=m.activity_key,
                scope=m.scope,
                category_code=m.category_code,
                quantity=_as_float(m.quantity),
                unit=m.unit,
                description=(m.description or "")[:500],
                region=deriv.region if deriv is not None else None,
                confidence=verdict.confidence,
                band=verdict.band,
                status=RowStatus(verdict.status),
                pcaf_data_quality=verdict.pcaf_data_quality,
                measurement_tier=verdict.tier,
                reasons=verdict.reasons,
                provenance=prov,
            )
            session.add(staged)
            await session.flush()  # assign staged.id for question FK
            all_staged.append(staged)
            sheet_staged += 1

            by_band[verdict.band] = by_band.get(verdict.band, 0) + 1
            by_tier[verdict.tier] = by_tier.get(verdict.tier, 0) + 1
            if m.scope:
                key = f"scope_{m.scope}"
                by_scope[key] = by_scope.get(key, 0) + 1

            # Accumulate a clarifying question into its GROUP (deduped across rows).
            # We only ask about real blockers — an unmatched activity, a mapper that
            # flagged its own pick, or a unit that doesn't fit the factor. Confident
            # rows are never questioned; neither are rows with NO quantity at all
            # (template scaffolding, to-be-filled rows) — there is no number to fix,
            # so they stage as gaps instead of interrogating the client.
            spec = (
                _question_spec(cat, grounding, m)
                if m.quantity not in (None, 0)
                else None
            )
            if spec is not None:
                grp = question_groups.setdefault(
                    spec["group_key"],
                    {
                        "question": spec["question"],
                        "field": spec["field"],
                        "choices": spec["choices"],
                        "row_ids": [],
                        "category_code": staged.category_code,
                    },
                )
                grp["row_ids"].append(staged.id)

            # Derivation questions — only the materially-significant assumptions
            # (round-trip ×2 grouped confirm, long-haul cabin class, missing
            # freight mass). These bypass the no-quantity gate above: a freight
            # row awaiting its mass HAS no quantity yet, that's the point.
            if deriv is not None:
                for dspec in deriv.questions:
                    grp = question_groups.setdefault(
                        dspec["group_key"],
                        {
                            "question": dspec["question"],
                            "field": dspec["field"],
                            "choices": dspec["choices"],
                            "row_ids": [],
                            "category_code": staged.category_code,
                        },
                    )
                    grp["row_ids"].append(staged.id)

        sheets_summary.append(
            {
                "sheet": table.sheet,
                "rows": table.row_count,
                "staged": sheet_staged,
                "detected_scope": table.detected_scope,
            }
        )

    # Plausibility pass (§4 of the verification spec) — needs the WHOLE batch,
    # so it runs after staging: value sanity, magnitude ceilings, in-batch
    # outliers, and drift vs what this org committed last period.
    prior_totals = await _prior_period_totals(session, ingestion)
    plausibility_flags = check_batch(all_staged, prior_totals)
    if plausibility_flags:
        by_band = {"green": 0, "amber": 0, "red": 0}
        for r in all_staged:
            by_band[r.band] = by_band.get(r.band, 0) + 1

    # Emit ONE question per group (largest groups first — those move the most rows).
    for grp in sorted(
        question_groups.values(), key=lambda g: len(g["row_ids"]), reverse=True
    ):
        row_ids = grp["row_ids"]
        n = len(row_ids)
        text = grp["question"]
        if n > 1:
            text = f"{text} (applies to {n} rows)"
        session.add(
            ClarificationQuestion(
                session_id=ingestion.id,
                staged_row_id=row_ids[0],  # representative row
                question=text[:1000],
                field=grp["field"],
                choices=grp["choices"],
                applies_to_row_ids=[str(rid) for rid in row_ids],
                category_code=grp["category_code"],
            )
        )
        questions += 1

    ingestion.total_rows = total
    ingestion.mapped_rows = mapped
    ingestion.question_count = questions
    ingestion.open_question_count = questions
    ingestion.committed_count = 0
    summary = {
        "sheets": sheets_summary,
        "by_scope": by_scope,
        "by_band": by_band,
        "by_tier": by_tier,
        "security": security,
        "mode": parse_mode,
        "plausibility_flags": plausibility_flags,
    }
    # Sheets skipped as empty/metadata-only — surfaced so nothing vanishes silently.
    if skipped_sheets:
        summary["skipped_sheets"] = skipped_sheets
    if parse_mode == "template":
        summary["notice"] = (
            "Recognised the CLIMATRIX template — mapped deterministically, no AI "
            "guessing needed."
        )
    # Empty result — explain WHY instead of silently showing "0 rows read".
    if total == 0:
        if not tables:
            summary["notice"] = (
                "We opened your file but every sheet looked like instructions or was "
                "empty — no data rows to import. If this is the CLIMATRIX template, "
                "enter your data beneath the grey SAMPLE row on each scope sheet and "
                "re-upload."
            )
        else:
            summary["notice"] = (
                "We read your file but found no fillable data rows (only sample or "
                "empty rows). Add your data and re-upload."
            )
    ingestion.summary = summary
    ingestion.status = (
        IngestionStatus.NEEDS_ANSWERS if questions else IngestionStatus.READY_FOR_REVIEW
    )
    ingestion.updated_at = datetime.utcnow()
    await session.flush()
    return ingestion


async def apply_answers(
    session: AsyncSession,
    ingestion: IngestionSession,
    answers: dict[UUID, str],
    *,
    region: str = "Global",
    year: int | None = None,
) -> IngestionSession:
    """Apply client answers to open questions and re-score the affected rows.

    When an answer carries a concrete correction (a unit, a quantity, or a valid
    activity key) it is applied and the row is re-grounded + re-scored. Otherwise
    the answer is recorded and, once a row has no open questions left, it moves
    from 'blocked' to 'needs review' so a human still confirms it.
    """
    year, year_assumed = _resolve_year(year)
    cat = await catalog_mod.build_from_db(session)
    touched_rows: set[UUID] = set()

    for qid, answer in answers.items():
        q = await session.get(ClarificationQuestion, qid)
        if q is None or q.session_id != ingestion.id:
            continue
        q.answer = (answer or "")[:1000]
        q.answered = True
        q.answered_at = datetime.utcnow()

        # One answer resolves every row in the group (all "PP" rows at once).
        row_ids = list(q.applies_to_row_ids or [])
        if not row_ids and q.staged_row_id:
            row_ids = [str(q.staged_row_id)]
        for rid in row_ids:
            row = await session.get(StagedRow, UUID(str(rid)))
            if row is None:
                continue
            _apply_answer_to_row(row, q.field, answer, cat)
            touched_rows.add(row.id)

    # Re-ground + re-score every touched row.
    for rid in touched_rows:
        row = await session.get(StagedRow, rid)
        if row is None:
            continue
        await _reground_row(
            session, row, cat, region=region, year=year, year_assumed=year_assumed
        )

    # Recompute open-question count and overall status.
    open_qs = (
        (
            await session.execute(
                select(ClarificationQuestion).where(
                    ClarificationQuestion.session_id == ingestion.id,
                    ClarificationQuestion.answered == False,  # noqa: E712
                )
            )
        )
        .scalars()
        .all()
    )
    ingestion.open_question_count = len(open_qs)
    ingestion.status = (
        IngestionStatus.NEEDS_ANSWERS if open_qs else IngestionStatus.READY_FOR_REVIEW
    )
    ingestion.updated_at = datetime.utcnow()
    await session.flush()
    return ingestion


async def commit_session(
    session: AsyncSession,
    ingestion: IngestionSession,
    *,
    reporting_period_id: UUID | None = None,
    allowed_scopes: set[int] | None = None,
) -> IngestionSession:
    """Write approved/ready staged rows into real Activity + Emission records.

    Each row is run through the same CalculationPipeline used everywhere else, so
    imported emissions are computed identically to manual entries. Rows that fail
    calculation are left un-committed with a ``commit_error`` for the review grid.
    """
    period_id = reporting_period_id or ingestion.reporting_period_id
    if period_id is None:
        raise ValueError("A reporting period is required before committing an import.")

    period = await session.get(ReportingPeriod, period_id)
    org = await session.get(Organization, ingestion.organization_id)
    if period is None or org is None:
        raise ValueError("Reporting period or organization not found.")

    site = await session.get(Site, ingestion.site_id) if ingestion.site_id else None
    if site is not None and site.organization_id != ingestion.organization_id:
        site = None
    region = base_factor_region(org, site)
    year = period.start_date.year if period.start_date else datetime.utcnow().year
    activity_date: date = period.start_date or date(year, 1, 1)

    ingestion.status = IngestionStatus.COMMITTING
    await session.flush()

    rows = (
        (
            await session.execute(
                select(StagedRow).where(
                    StagedRow.session_id == ingestion.id,
                    StagedRow.status.in_([s.value for s in _COMMITTABLE]),
                )
            )
        )
        .scalars()
        .all()
    )

    batch = ImportBatch(
        organization_id=ingestion.organization_id,
        reporting_period_id=period_id,
        file_name=ingestion.filename,
        file_type=(
            ingestion.filename.rsplit(".", 1)[-1]
            if "." in ingestion.filename
            else "csv"
        ),
        file_size_bytes=ingestion.file_size_bytes,
        status=ImportBatchStatus.PROCESSING,
        total_rows=len(rows),
        uploaded_by=ingestion.created_by,
    )
    session.add(batch)
    await session.flush()

    pipeline = CalculationPipeline(session)
    committed = 0
    failed = 0
    committed_by_hub: dict[str, int] = {}

    for row in rows:
        if not row.activity_key or row.quantity is None or not row.unit:
            row.commit_error = "Missing activity, quantity, or unit."
            failed += 1
            continue
        if row.scope not in (1, 2, 3) or not row.category_code:
            # Never let a row with an invalid/absent scope reach the ledger — an
            # Activity with scope=0 would corrupt every downstream scope rollup.
            row.commit_error = "Invalid or missing scope/category."
            failed += 1
            continue
        if allowed_scopes is not None and row.scope not in allowed_scopes:
            # Plan gate (Starter = Scope 1+2): the row stays visible in review
            # with an honest reason — the value-chain upsell, never a silent drop.
            row.commit_error = (
                f"Scope {row.scope} rows need the Professional plan — "
                "your value chain is parsed and waiting, upgrade to commit it."
            )
            failed += 1
            continue
        try:
            calc = await pipeline.calculate(
                ActivityInput(
                    activity_key=row.activity_key,
                    quantity=Decimal(str(row.quantity)),
                    unit=row.unit,
                    scope=row.scope or 0,
                    category_code=row.category_code or "",
                    # A row-level region (e.g. a hotel's stay country) beats the
                    # org default — that's how "nights × the STAY country's
                    # factor" actually selects the country factor.
                    region=row.region or region,
                    year=year,
                )
            )
        except (FactorNotFoundError, UnitConversionError, CalculationError) as exc:
            row.commit_error = f"{type(exc).__name__}: {exc}"[:500]
            failed += 1
            continue
        except Exception as exc:  # unexpected — record per-row, don't abort the batch
            row.commit_error = f"Unexpected: {type(exc).__name__}: {exc}"[:500]
            failed += 1
            continue

        # A derived quantity carries its assumptions onto the committed
        # activity's quality justification — the validator-facing "why".
        deriv_state = (
            row.provenance.get("derivation")
            if isinstance(row.provenance, dict)
            else None
        )
        justification = None
        if deriv_state and deriv_state.get("assumptions"):
            justification = "; ".join(deriv_state["assumptions"])[:500]

        activity = Activity(
            organization_id=ingestion.organization_id,
            reporting_period_id=period_id,
            scope=row.scope or 0,
            category_code=row.category_code or "",
            activity_key=row.activity_key,
            description=row.description or "",
            quantity=Decimal(str(row.quantity)),
            unit=row.unit,
            activity_date=activity_date,
            site_id=site.id if site is not None else None,
            # A row-level region (hotel stay country) is the activity's own
            # context; the site's region is reconstructable from site_id, so
            # only the row override is persisted here.
            region=row.region or None,
            created_by=ingestion.created_by,
            data_source=DataSource.IMPORT,
            import_batch_id=batch.id,
            data_quality_score=row.pcaf_data_quality or 4,
            data_quality_justification=justification,
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
                biogenic_co2_kg=calc.biogenic_co2_kg,
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
        # Keep the staged audit trail honest: the pipeline may resolve a different
        # factor at commit time (period year/region) than the one shown at review.
        # The provenance dict must describe what was actually committed.
        prov = dict(row.provenance or {})
        prov["factor_source"] = calc.factor_source or prov.get("factor_source")
        prov["factor_year"] = calc.factor_year
        prov["factor_region"] = calc.factor_region or prov.get("factor_region")
        prov["factor_name"] = calc.factor_display_name or prov.get("factor_name")
        prov["method"] = calc.resolution_strategy
        prov["method_label"] = _METHOD_LABEL.get(
            calc.resolution_strategy, calc.resolution_strategy
        )
        row.provenance = prov

        row.committed_activity_id = activity.id
        row.status = RowStatus.COMMITTED
        row.commit_error = None
        row.updated_at = datetime.utcnow()
        committed += 1

        hub_code = HUB_CODE_FOR.get(row.category_code or "")
        if hub_code:
            committed_by_hub[hub_code] = committed_by_hub.get(hub_code, 0) + 1

    batch.status = (
        ImportBatchStatus.COMPLETED if failed == 0 else ImportBatchStatus.PARTIAL
    )
    batch.successful_rows = committed
    batch.failed_rows = failed
    batch.completed_at = datetime.utcnow()

    # Upload-driven relevance: what just committed is evidence about the org's
    # inventory map — fold it into the category profile and surface the result
    # (chips + exclusion conflicts) on the commit success panel via summary.
    updates, conflicts = await _sync_category_profile(
        session, ingestion, committed_by_hub
    )
    summary = dict(ingestion.summary or {})
    summary["profile_updates"] = updates
    summary["profile_conflicts"] = conflicts
    ingestion.summary = summary

    ingestion.import_batch_id = batch.id
    ingestion.committed_count = committed
    ingestion.status = IngestionStatus.COMMITTED
    ingestion.updated_at = datetime.utcnow()
    await session.flush()
    return ingestion


async def _sync_category_profile(
    session: AsyncSession,
    ingestion: IngestionSession,
    committed_by_hub: dict[str, int],
) -> tuple[list[dict], list[dict]]:
    """Committed data upgrades the org's inventory map (approve-by-exception).

    For each hub category that just received committed rows, an unset or
    not-sure org-level profile row is auto-marked ``relevant`` with upload
    provenance; the success panel lets the user un-tick (back to not-sure).
    Uploads only ever UPGRADE certainty: a documented exclusion
    (``not_relevant``) is an auditor-facing decision and is never auto-flipped
    — it raises a conflict entry instead. A category un-ticked against this
    session's evidence is not re-suggested by the same session.
    """
    updates: list[dict] = []
    conflicts: list[dict] = []
    if not committed_by_hub:
        return updates, conflicts

    profiles: dict[str, CategoryProfile] = {
        p.category_code: p
        for p in (
            (
                await session.execute(
                    select(CategoryProfile).where(
                        CategoryProfile.organization_id == ingestion.organization_id,
                        CategoryProfile.site_id.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
    }
    now = datetime.utcnow()
    for hub_code in sorted(committed_by_hub, key=_category_sort_key):
        cat = CATEGORY_BY_CODE.get(hub_code)
        if cat is None:
            continue
        row_count = committed_by_hub[hub_code]
        profile = profiles.get(hub_code)
        relevance = None
        if profile is not None:
            relevance = (
                profile.relevance.value
                if isinstance(profile.relevance, CategoryRelevance)
                else profile.relevance
            )

        if relevance == CategoryRelevance.RELEVANT.value:
            continue  # already declared — coverage numbers update as today
        if relevance == CategoryRelevance.NOT_RELEVANT.value:
            conflicts.append(
                {
                    "category_code": hub_code,
                    "name": cat["name"],
                    "row_count": row_count,
                    "exclusion_reason": profile.exclusion_reason,
                }
            )
            continue

        details = dict(profile.details or {}) if profile is not None else {}
        if str(ingestion.id) in (details.get("relevance_dismissed_sessions") or []):
            continue
        details["relevance_provenance"] = {
            "source": "upload",
            "session_id": str(ingestion.id),
            "filename": ingestion.filename,
            "at": now.isoformat(),
        }
        if profile is None:
            profile = CategoryProfile(
                organization_id=ingestion.organization_id,
                site_id=None,
                scope=cat["scope"],
                category_code=hub_code,
                relevance=CategoryRelevance.RELEVANT.value,
                details=details,
                updated_at=now,
            )
            session.add(profile)
        else:
            profile.relevance = CategoryRelevance.RELEVANT.value
            profile.details = details
            profile.updated_at = now
        updates.append(
            {
                "category_code": hub_code,
                "name": cat["name"],
                "row_count": row_count,
                "previous_relevance": relevance,
            }
        )
    return updates, conflicts


def _category_sort_key(code: str) -> tuple:
    """'3.10' sorts after '3.9' — numeric, not lexicographic."""
    try:
        return tuple(int(part) for part in code.split("."))
    except ValueError:
        return (99, code)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _as_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _json_safe_dict(d: dict | None) -> dict:
    if not d:
        return {}
    out = {}
    for k, v in d.items():
        out[str(k)] = (
            v if (v is None or isinstance(v, (str, int, float, bool))) else str(v)
        )
    return out


# Explicit "I don't know / leave it out" answer. Non-empty on purpose so it
# survives the client's "did they answer?" filter and means "make this a gap".
_GAP_ANSWER = "__leave_gap__"


def _norm(s: str | None) -> str:
    """Group key normaliser — lowercase, collapse whitespace."""
    return " ".join((s or "").lower().split())


def _choice_label(entry) -> str:
    """Human label for an activity choice: real-world name + the canonical key."""
    name = (getattr(entry, "display_name", "") or "").strip()
    if name and name.lower() != entry.activity_key.lower():
        return f"{name} · {entry.activity_key}"
    return entry.activity_key


def _activity_choices(cat, description: str, picked: str | None) -> list[dict]:
    """Candidate activity keys for a mapping/confirm question, picked one first."""
    seen: set[str] = set()
    choices: list[dict] = []
    if picked and cat.is_real(picked):
        entry = cat.get(picked)
        choices.append({"value": picked, "label": _choice_label(entry)})
        seen.add(picked)
    for entry in cat.search(description, top_n=6):
        if entry.activity_key in seen:
            continue
        seen.add(entry.activity_key)
        choices.append({"value": entry.activity_key, "label": _choice_label(entry)})
        if len(choices) >= 6:
            break
    choices.append({"value": _GAP_ANSWER, "label": "None of these — leave as a gap"})
    return choices


async def _prior_period_totals(
    session: AsyncSession, ingestion: IngestionSession
) -> dict[str, float]:
    """Committed quantity per activity_key in the most recent PRIOR period of
    this org — the baseline the consistency check compares against."""
    if not ingestion.reporting_period_id:
        return {}
    current = await session.get(ReportingPeriod, ingestion.reporting_period_id)
    if current is None:
        return {}
    prior = (
        await session.execute(
            select(ReportingPeriod)
            .where(
                ReportingPeriod.organization_id == ingestion.organization_id,
                ReportingPeriod.start_date < current.start_date,
            )
            .order_by(ReportingPeriod.start_date.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if prior is None:
        return {}
    rows = (
        await session.execute(
            select(Activity.activity_key, func.sum(Activity.quantity))
            .where(Activity.reporting_period_id == prior.id)
            .group_by(Activity.activity_key)
        )
    ).all()
    return {key: float(total or 0) for key, total in rows}


def _question_spec(cat, grounding: GroundingVerdict, m) -> dict | None:
    """Build a grouped, typed clarifying question for a row — or None if the row is
    confident enough to need no question. The group_key dedupes identical issues so
    every "PP" row (or every diesel-in-liters row) is asked about exactly once."""
    desc = (m.description or "").strip()

    # 1) Activity couldn't be matched at all — offer real candidates to pick from.
    if not grounding.resolved:
        return {
            "group_key": f"map:{_norm(desc)}",
            "field": "activity",
            "choices": _activity_choices(cat, desc, m.activity_key),
            "question": f'Which activity type is "{desc or "this row"}"?',
        }

    # 2) Mapped, but the unit doesn't fit the factor — expected vs. as-given.
    if not grounding.unit_ok:
        expected = grounding.factor_unit or "the factor's unit"
        given = m.unit or "(none)"
        choices = [{"value": expected, "label": f"{expected} — expected by the factor"}]
        if given and _norm(given) != _norm(expected):
            choices.append({"value": given, "label": f"{given} — as in your file"})
        return {
            "group_key": f"unit:{m.activity_key}:{_norm(given)}",
            "field": "unit",
            "choices": choices,
            "question": (
                f'"{desc or "This row"}" is recorded in "{given}", but the factor '
                f"expects {expected}. Which unit is correct?"
            ),
        }

    # 3) Mapped cleanly, but the mapper flagged its own pick — a quick confirm.
    if m.question:
        picked_entry = cat.get(m.activity_key)
        picked_label = _choice_label(picked_entry) if picked_entry else m.activity_key
        return {
            "group_key": f"map:{_norm(desc)}",
            "field": "activity",
            "choices": _activity_choices(cat, desc, m.activity_key),
            "question": f'We mapped "{desc}" to {picked_label}. Is that right?',
        }

    return None


def _apply_answer_to_row(row: StagedRow, field: str | None, answer: str, cat) -> None:
    """Apply a concrete answer to a staged row (best-effort, safe on garbage input)."""
    answer = (answer or "").strip()
    if not answer:
        return
    # Derivation questions (round-trip confirm, freight mass) recompute the
    # quantity deterministically from the stored derivation state.
    deriv_state = (
        row.provenance.get("derivation") if isinstance(row.provenance, dict) else None
    )
    if field == "quantity" and deriv_state:
        if apply_derivation_answer(row, deriv_state, answer):
            return
    if field == "unit":
        row.unit = answer[:50]
    elif field == "quantity":
        try:
            row.quantity = float(answer.replace(",", ""))
        except (ValueError, InvalidOperation):
            pass
    elif field == "activity":
        if answer == _GAP_ANSWER:
            # Client chose "leave as a gap" — clear any tentative mapping so the row
            # is honestly a gap rather than a guessed factor.
            row.activity_key = None
            row.scope = None
            row.category_code = None
        elif cat.is_real(answer):
            # Accept only a real catalog key; pull scope/category from the entry.
            entry = cat.get(answer)
            row.activity_key = answer
            if entry:
                row.scope = entry.scope
                row.category_code = entry.category_code


async def reground_row(
    session: AsyncSession,
    row: StagedRow,
    *,
    region: str = "Global",
    year: int | None = None,
) -> StagedRow:
    """Public: re-ground + re-score a single staged row after a manual edit.

    A hand-edit to activity_key / unit / quantity must never keep the old
    confidence band or status — the review grid would then lie about how sure we
    are. This recomputes everything from the edited values (building the catalog
    fresh so a newly-chosen activity_key resolves correctly)."""
    year, year_assumed = _resolve_year(year)
    cat = await catalog_mod.build_from_db(session)
    await _reground_row(
        session, row, cat, region=region, year=year, year_assumed=year_assumed
    )
    return row


async def _reground_row(
    session: AsyncSession,
    row: StagedRow,
    cat,
    *,
    region: str,
    year: int,
    year_assumed: bool = False,
) -> None:
    if row.activity_key:
        # Scope/category are authoritative from the catalog entry for this key —
        # never left to whatever a hand-edit or the LLM put on the row.
        entry = cat.get(row.activity_key)
        if entry:
            row.scope = entry.scope
            row.category_code = entry.category_code
        grounding = await ground_row(
            session,
            row.activity_key,
            row.unit or "",
            region=row.region or region,
            year=year,
        )
        violations = check_row(
            cat, row.activity_key, row.scope or 0, row.category_code or ""
        )
    else:
        grounding = _no_key_verdict("Still needs an activity type.")
        violations = []

    # Derivation state must survive a re-ground: the rebuilt provenance below
    # would otherwise drop it, and with it the ESTIMATED floor + audit trail.
    deriv_state = (
        row.provenance.get("derivation") if isinstance(row.provenance, dict) else None
    )

    verdict = score_row(grounding, violations, llm_self_score=max(row.confidence, 0.6))
    if year_assumed and row.activity_key:
        verdict.reasons.append(_year_assumed_reason(year))
    if deriv_state:
        verdict.pcaf_data_quality = max(verdict.pcaf_data_quality or 4, 4)
        if row.quantity is not None and verdict.tier != "gap":
            verdict.tier = "estimated"
        verdict.reasons = list(verdict.reasons) + list(
            deriv_state.get("assumptions") or []
        )
    row.confidence = verdict.confidence
    row.band = verdict.band
    row.pcaf_data_quality = verdict.pcaf_data_quality
    row.measurement_tier = verdict.tier
    row.reasons = verdict.reasons
    prov = _provenance(grounding, row.unit)
    if deriv_state:
        prov["derivation"] = deriv_state
    row.provenance = prov
    # Once answered, a previously-blocked row moves to human review (not auto-ready).
    row.status = (
        RowStatus.NEEDS_REVIEW
        if verdict.status in ("ready", "needs_review")
        else RowStatus(verdict.status)
    )
    row.updated_at = datetime.utcnow()
