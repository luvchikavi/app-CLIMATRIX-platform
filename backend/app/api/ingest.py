"""Ingestion API — the "drop any file" funnel.

    POST   /api/ingest                 upload a file → parse → stage rows + questions
    GET    /api/ingest                 list recent ingestion sessions (this org)
    GET    /api/ingest/{id}            full review payload (rows + open questions)
    POST   /api/ingest/{id}/answers    answer clarifying questions → re-score rows
    PATCH  /api/ingest/{id}/rows/{rid} approve / reject / edit a staged row
    POST   /api/ingest/{id}/commit     write approved rows into the emissions ledger

Every upload passes the security guard before a byte is parsed, and every row is
mapped/grounded/scored server-side. The client only ever confirms — it never has
to reshape its data to fit the app.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.config import settings
from app.database import get_session
from app.models.core import Organization, ReportingPeriod, User
from app.models.ingestion import (
    ClarificationQuestion,
    IngestionSession,
    IngestionStatus,
    RowStatus,
    StagedRow,
)
from app.services.ingestion import orchestrator
from app.services.ingestion.file_guard import FileRejected, check_upload

router = APIRouter()

_MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024

# Temp dir for files handed off to the worker (cleaned up once the job reads them).
_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "ingest")
os.makedirs(_UPLOAD_DIR, exist_ok=True)


def _upload_path(session_id: UUID, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "dat"
    return os.path.join(_UPLOAD_DIR, f"{session_id}.{ext}")


def _persist_upload(session_id: UUID, content: bytes, filename: str) -> str:
    path = _upload_path(session_id, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path


def _cleanup_upload(session_id: UUID, filename: str) -> None:
    path = _upload_path(session_id, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# response schemas
# ---------------------------------------------------------------------------


class QuestionOut(BaseModel):
    id: UUID
    staged_row_id: Optional[UUID]
    question: str
    field: Optional[str]
    choices: Optional[list]
    answer: Optional[str]
    answered: bool
    applies_count: int = 1


class StagedRowOut(BaseModel):
    id: UUID
    sheet: str
    row_index: int
    source: Optional[dict]
    activity_key: Optional[str]
    scope: Optional[int]
    category_code: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    description: str
    confidence: float
    band: str
    status: str
    pcaf_data_quality: Optional[int]
    measurement_tier: Optional[str]
    reasons: Optional[list]
    provenance: Optional[dict]
    committed_activity_id: Optional[UUID]
    commit_error: Optional[str]


class SessionOut(BaseModel):
    id: UUID
    filename: str
    status: str
    total_rows: int
    mapped_rows: int
    question_count: int
    open_question_count: int
    committed_count: int
    summary: Optional[dict]
    error_message: Optional[str]
    reporting_period_id: Optional[UUID]
    import_batch_id: Optional[UUID]
    created_at: datetime


class SessionDetailOut(SessionOut):
    rows: list[StagedRowOut]
    questions: list[QuestionOut]


def _session_out(s: IngestionSession) -> SessionOut:
    return SessionOut(
        id=s.id,
        filename=s.filename,
        status=s.status.value if hasattr(s.status, "value") else str(s.status),
        total_rows=s.total_rows,
        mapped_rows=s.mapped_rows,
        question_count=s.question_count,
        open_question_count=s.open_question_count,
        committed_count=s.committed_count,
        summary=s.summary,
        error_message=s.error_message,
        reporting_period_id=s.reporting_period_id,
        import_batch_id=s.import_batch_id,
        created_at=s.created_at,
    )


def _row_out(r: StagedRow) -> StagedRowOut:
    return StagedRowOut(
        id=r.id,
        sheet=r.sheet,
        row_index=r.row_index,
        source=r.source,
        activity_key=r.activity_key,
        scope=r.scope,
        category_code=r.category_code,
        quantity=r.quantity,
        unit=r.unit,
        description=r.description,
        confidence=r.confidence,
        band=r.band,
        status=r.status.value if hasattr(r.status, "value") else str(r.status),
        pcaf_data_quality=r.pcaf_data_quality,
        measurement_tier=r.measurement_tier,
        reasons=r.reasons,
        provenance=r.provenance,
        committed_activity_id=r.committed_activity_id,
        commit_error=r.commit_error,
    )


def _question_out(q: ClarificationQuestion) -> QuestionOut:
    return QuestionOut(
        id=q.id,
        staged_row_id=q.staged_row_id,
        question=q.question,
        field=q.field,
        choices=q.choices,
        answer=q.answer,
        answered=q.answered,
        applies_count=len(q.applies_to_row_ids or []) or 1,
    )


async def _get_owned_session(
    session_id: UUID, session: AsyncSession, user: User
) -> IngestionSession:
    obj = await session.get(IngestionSession, session_id)
    if obj is None or obj.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Ingestion session not found.")
    return obj


# ---------------------------------------------------------------------------
# request bodies
# ---------------------------------------------------------------------------


class AnswerItem(BaseModel):
    question_id: UUID
    answer: str


class AnswersBody(BaseModel):
    answers: list[AnswerItem]


class RowPatchBody(BaseModel):
    status: Optional[str] = None  # approved | rejected | needs_review
    activity_key: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None


class CommitBody(BaseModel):
    reporting_period_id: Optional[UUID] = None


# ---------------------------------------------------------------------------
# endpoints
# ---------------------------------------------------------------------------


@router.post("/ingest", response_model=SessionDetailOut)
async def upload_and_analyze(
    request: Request,
    file: UploadFile = File(...),
    reporting_period_id: Optional[UUID] = Form(default=None),
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Upload a file, security-check it, and parse it into staged rows + questions.

    In production/staging the parse runs on the arq worker (upload returns instantly
    with status 'analyzing'; the client polls GET /ingest/{id}). Everywhere else — or
    if the queue is unreachable — it runs inline so dev/test stay self-contained.
    """
    content = await file.read()
    try:
        report = check_upload(content, file.filename or "upload", max_bytes=_MAX_BYTES)
    except FileRejected as exc:
        raise HTTPException(status_code=400, detail=exc.message)

    content_hash = hashlib.sha256(content).hexdigest()

    # Resolve region/year context from the org + (optional) reporting period.
    org = await session.get(Organization, current_user.organization_id)
    region = (org.default_region if org else None) or "Global"
    year = 2024
    if reporting_period_id:
        period = await session.get(ReportingPeriod, reporting_period_id)
        if period is None or period.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Reporting period not found.")
        if period.start_date:
            year = period.start_date.year

    ingestion = IngestionSession(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        reporting_period_id=reporting_period_id,
        filename=report.filename,
        file_size_bytes=report.size_bytes,
        content_hash=content_hash,
    )
    session.add(ingestion)
    await session.flush()

    # Dispatch parsing to the arq worker only when explicitly enabled and a worker
    # is deployed. Off by default — the parser is fast (~15-20s), so we parse inline
    # in the request, which is reliable without any worker infrastructure.
    if settings.ingest_use_worker:
        try:
            file_path = _persist_upload(ingestion.id, content, report.filename)
            redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
            await redis.enqueue_job(
                "analyze_ingestion_session",
                str(ingestion.id),
                file_path,
                report.filename,
                region,
                year,
            )
            ingestion.status = IngestionStatus.ANALYZING
            await session.commit()
            return await _detail(session, ingestion)
        except Exception:
            # Queue unreachable — clean up the temp file and parse inline below.
            _cleanup_upload(ingestion.id, report.filename)

    await orchestrator.run_analysis(
        session, ingestion, content, report.filename, region=region, year=year
    )
    await orchestrator.annotate_duplicate(session, ingestion)
    await session.commit()

    return await _detail(session, ingestion)


@router.get("/ingest", response_model=list[SessionOut])
async def list_sessions(
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    rows = (
        (
            await session.execute(
                select(IngestionSession)
                .where(IngestionSession.organization_id == current_user.organization_id)
                .order_by(IngestionSession.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    return [_session_out(s) for s in rows]


@router.get("/ingest/{session_id}", response_model=SessionDetailOut)
async def get_session_detail(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    ingestion = await _get_owned_session(session_id, session, current_user)
    return await _detail(session, ingestion)


@router.post("/ingest/{session_id}/answers", response_model=SessionDetailOut)
async def answer_questions(
    session_id: UUID,
    body: AnswersBody,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    ingestion = await _get_owned_session(session_id, session, current_user)
    org = await session.get(Organization, current_user.organization_id)
    region = (org.default_region if org else None) or "Global"
    answers = {a.question_id: a.answer for a in body.answers}
    await orchestrator.apply_answers(session, ingestion, answers, region=region)
    await session.commit()
    return await _detail(session, ingestion)


@router.patch("/ingest/{session_id}/rows/{row_id}", response_model=StagedRowOut)
async def patch_row(
    session_id: UUID,
    row_id: UUID,
    body: RowPatchBody,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Approve / reject / lightly edit a staged row from the review grid."""
    ingestion = await _get_owned_session(session_id, session, current_user)
    row = await session.get(StagedRow, row_id)
    if row is None or row.session_id != ingestion.id:
        raise HTTPException(status_code=404, detail="Row not found.")
    if row.status == RowStatus.COMMITTED:
        raise HTTPException(status_code=409, detail="Row is already committed.")

    data_edited = False
    if body.activity_key is not None:
        row.activity_key = body.activity_key
        data_edited = True
    if body.quantity is not None:
        row.quantity = body.quantity
        data_edited = True
    if body.unit is not None:
        row.unit = body.unit
        data_edited = True

    # A hand-edit to activity/unit/quantity must re-ground + re-score — otherwise the
    # grid keeps a stale confidence band that no longer reflects the edited values.
    if data_edited:
        org = await session.get(Organization, current_user.organization_id)
        region = (org.default_region if org else None) or "Global"
        await orchestrator.reground_row(session, row, region=region)

    # An explicit status change (Keep/Drop) always wins over the re-grounded status.
    if body.status is not None:
        try:
            row.status = RowStatus(body.status)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid status '{body.status}'."
            )
    row.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(row)
    return _row_out(row)


@router.post("/ingest/{session_id}/commit", response_model=SessionDetailOut)
async def commit(
    session_id: UUID,
    body: CommitBody | None = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    ingestion = await _get_owned_session(session_id, session, current_user)
    period_id = (
        body.reporting_period_id if body else None
    ) or ingestion.reporting_period_id
    if period_id is None:
        raise HTTPException(
            status_code=400,
            detail="Select a reporting period before committing this import.",
        )
    period = await session.get(ReportingPeriod, period_id)
    if period is None or period.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Reporting period not found.")

    try:
        await orchestrator.commit_session(
            session, ingestion, reporting_period_id=period_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await session.commit()
    return await _detail(session, ingestion)


async def _detail(
    session: AsyncSession, ingestion: IngestionSession
) -> SessionDetailOut:
    rows = (
        (
            await session.execute(
                select(StagedRow)
                .where(StagedRow.session_id == ingestion.id)
                .order_by(StagedRow.sheet, StagedRow.row_index)
            )
        )
        .scalars()
        .all()
    )
    questions = (
        (
            await session.execute(
                select(ClarificationQuestion)
                .where(ClarificationQuestion.session_id == ingestion.id)
                .order_by(
                    ClarificationQuestion.answered, ClarificationQuestion.created_at
                )
            )
        )
        .scalars()
        .all()
    )
    base = _session_out(ingestion)
    return SessionDetailOut(
        **base.model_dump(),
        rows=[_row_out(r) for r in rows],
        questions=[_question_out(q) for q in questions],
    )
