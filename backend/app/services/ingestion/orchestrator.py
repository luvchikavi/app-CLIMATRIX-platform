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

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Organization, ReportingPeriod
from app.models.emission import (
    Activity,
    DataSource,
    Emission,
    ConfidenceLevel,
    ImportBatch,
    ImportBatchStatus,
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
from app.services.calculation.resolver import FactorNotFoundError
from app.services.calculation.normalizer import UnitConversionError
from app.services.ingestion import catalog as catalog_mod
from app.services.ingestion.confidence import score_row
from app.services.ingestion.file_guard import sanitise_rows, scan_text_for_injection
from app.services.ingestion.grounding import GroundingVerdict, ground_row
from app.services.ingestion.loader import load
from app.services.ingestion.mapper import map_table
from app.services.ingestion.rule_engine import check_row

# Statuses that a commit will actually write to the ledger.
_COMMITTABLE = {RowStatus.READY, RowStatus.APPROVED}


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
    year: int = 2024,
) -> IngestionSession:
    """Parse an upload into staged rows + clarifying questions.

    Deterministic apart from the single LLM mapping call per sheet. On any
    unexpected failure the session is marked FAILED with a client-safe message
    rather than left half-done.
    """
    ingestion.status = IngestionStatus.ANALYZING
    ingestion.updated_at = datetime.utcnow()
    await session.flush()

    try:
        tables = load(content, filename)
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

    cat = await catalog_mod.build_from_db(session)

    total = 0
    mapped = 0
    questions = 0
    by_scope: dict[str, int] = {}
    by_band = {"green": 0, "amber": 0, "red": 0}
    sheets_summary: list[dict] = []
    security = {"formula_cells_sanitised": 0, "injection_flags": 0}

    for table in tables:
        # Scrub hostile cells (formula injection) before the LLM ever sees them.
        clean_rows, formula_hits, injection_hits = sanitise_rows(table.rows)
        table.rows = clean_rows
        security["formula_cells_sanitised"] += formula_hits
        security["injection_flags"] += injection_hits

        try:
            mapped_rows = map_table(table, cat, client=client)
        except Exception as exc:  # a bad sheet shouldn't kill the whole file
            sheets_summary.append(
                {"sheet": table.sheet, "rows": table.row_count, "error": str(exc)[:200]}
            )
            continue

        sheet_staged = 0
        for m in mapped_rows:
            total += 1
            if m.activity_key:
                mapped += 1
                grounding = await ground_row(
                    session, m.activity_key, m.unit or "", region=region, year=year
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
                confidence=verdict.confidence,
                band=verdict.band,
                status=RowStatus(verdict.status),
                pcaf_data_quality=verdict.pcaf_data_quality,
                reasons=verdict.reasons,
            )
            session.add(staged)
            await session.flush()  # assign staged.id for question FK
            sheet_staged += 1

            by_band[verdict.band] = by_band.get(verdict.band, 0) + 1
            if m.scope:
                key = f"scope_{m.scope}"
                by_scope[key] = by_scope.get(key, 0) + 1

            # A clarifying question if the mapper asked one OR the row is blocked.
            q_text = m.question
            if not q_text and verdict.status == RowStatus.NEEDS_QUESTION.value:
                q_text = _default_question(grounding, m)
            if q_text:
                session.add(
                    ClarificationQuestion(
                        session_id=ingestion.id,
                        staged_row_id=staged.id,
                        question=q_text[:1000],
                        field=_infer_field(grounding, m),
                    )
                )
                questions += 1

        sheets_summary.append(
            {
                "sheet": table.sheet,
                "rows": table.row_count,
                "staged": sheet_staged,
                "detected_scope": table.detected_scope,
            }
        )

    ingestion.total_rows = total
    ingestion.mapped_rows = mapped
    ingestion.question_count = questions
    ingestion.open_question_count = questions
    ingestion.committed_count = 0
    summary = {
        "sheets": sheets_summary,
        "by_scope": by_scope,
        "by_band": by_band,
        "security": security,
    }
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
    year: int = 2024,
) -> IngestionSession:
    """Apply client answers to open questions and re-score the affected rows.

    When an answer carries a concrete correction (a unit, a quantity, or a valid
    activity key) it is applied and the row is re-grounded + re-scored. Otherwise
    the answer is recorded and, once a row has no open questions left, it moves
    from 'blocked' to 'needs review' so a human still confirms it.
    """
    cat = await catalog_mod.build_from_db(session)
    touched_rows: set[UUID] = set()

    for qid, answer in answers.items():
        q = await session.get(ClarificationQuestion, qid)
        if q is None or q.session_id != ingestion.id:
            continue
        q.answer = (answer or "")[:1000]
        q.answered = True
        q.answered_at = datetime.utcnow()

        if not q.staged_row_id:
            continue
        row = await session.get(StagedRow, q.staged_row_id)
        if row is None:
            continue
        _apply_answer_to_row(row, q.field, answer, cat)
        touched_rows.add(row.id)

    # Re-ground + re-score every touched row.
    for rid in touched_rows:
        row = await session.get(StagedRow, rid)
        if row is None:
            continue
        await _reground_row(session, row, cat, region=region, year=year)

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

    region = org.default_region or "Global"
    year = period.start_date.year if period.start_date else 2024
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
        try:
            calc = await pipeline.calculate(
                ActivityInput(
                    activity_key=row.activity_key,
                    quantity=Decimal(str(row.quantity)),
                    unit=row.unit,
                    scope=row.scope or 0,
                    category_code=row.category_code or "",
                    region=region,
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
            created_by=ingestion.created_by,
            data_source=DataSource.IMPORT,
            import_batch_id=batch.id,
            data_quality_score=row.pcaf_data_quality or 4,
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
        row.committed_activity_id = activity.id
        row.status = RowStatus.COMMITTED
        row.commit_error = None
        row.updated_at = datetime.utcnow()
        committed += 1

    batch.status = (
        ImportBatchStatus.COMPLETED if failed == 0 else ImportBatchStatus.PARTIAL
    )
    batch.successful_rows = committed
    batch.failed_rows = failed
    batch.completed_at = datetime.utcnow()

    ingestion.import_batch_id = batch.id
    ingestion.committed_count = committed
    ingestion.status = IngestionStatus.COMMITTED
    ingestion.updated_at = datetime.utcnow()
    await session.flush()
    return ingestion


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


def _default_question(grounding: GroundingVerdict, m) -> str:
    if not grounding.resolved:
        return (
            f"We couldn't match \"{m.description or 'this row'}\" to an activity type. "
            "Which activity does it represent?"
        )
    if not grounding.unit_ok:
        return (
            f"The unit '{m.unit}' doesn't match what this factor expects "
            f"({grounding.factor_unit}). Which unit is correct?"
        )
    return "Please confirm this row before we include it."


def _infer_field(grounding: GroundingVerdict, m) -> str | None:
    if not grounding.resolved:
        return "activity"
    if not grounding.unit_ok:
        return "unit"
    return None


def _apply_answer_to_row(row: StagedRow, field: str | None, answer: str, cat) -> None:
    """Apply a concrete answer to a staged row (best-effort, safe on garbage input)."""
    answer = (answer or "").strip()
    if not answer:
        return
    if field == "unit":
        row.unit = answer[:50]
    elif field == "quantity":
        try:
            row.quantity = float(answer.replace(",", ""))
        except (ValueError, InvalidOperation):
            pass
    elif field == "activity":
        # Accept only a real catalog key; pull scope/category from the catalog entry.
        if cat.is_real(answer):
            entry = cat.get(answer)
            row.activity_key = answer
            if entry:
                row.scope = entry.scope
                row.category_code = entry.category_code


async def reground_row(
    session: AsyncSession, row: StagedRow, *, region: str = "Global", year: int = 2024
) -> StagedRow:
    """Public: re-ground + re-score a single staged row after a manual edit.

    A hand-edit to activity_key / unit / quantity must never keep the old
    confidence band or status — the review grid would then lie about how sure we
    are. This recomputes everything from the edited values (building the catalog
    fresh so a newly-chosen activity_key resolves correctly)."""
    cat = await catalog_mod.build_from_db(session)
    await _reground_row(session, row, cat, region=region, year=year)
    return row


async def _reground_row(
    session: AsyncSession, row: StagedRow, cat, *, region: str, year: int
) -> None:
    if row.activity_key:
        # Scope/category are authoritative from the catalog entry for this key —
        # never left to whatever a hand-edit or the LLM put on the row.
        entry = cat.get(row.activity_key)
        if entry:
            row.scope = entry.scope
            row.category_code = entry.category_code
        grounding = await ground_row(
            session, row.activity_key, row.unit or "", region=region, year=year
        )
        violations = check_row(
            cat, row.activity_key, row.scope or 0, row.category_code or ""
        )
    else:
        grounding = _no_key_verdict("Still needs an activity type.")
        violations = []

    verdict = score_row(grounding, violations, llm_self_score=max(row.confidence, 0.6))
    row.confidence = verdict.confidence
    row.band = verdict.band
    row.pcaf_data_quality = verdict.pcaf_data_quality
    row.reasons = verdict.reasons
    # Once answered, a previously-blocked row moves to human review (not auto-ready).
    row.status = (
        RowStatus.NEEDS_REVIEW
        if verdict.status in ("ready", "needs_review")
        else RowStatus(verdict.status)
    )
    row.updated_at = datetime.utcnow()
