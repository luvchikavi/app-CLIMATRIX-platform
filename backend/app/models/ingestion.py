"""Ingestion models — the staging layer behind the "drop any file" funnel.

An ``IngestionSession`` is one uploaded file working its way through the parser.
Every source row becomes a ``StagedRow`` (mapped, grounded, rule-checked, scored)
that a human reviews before it is committed into real ``Activity`` + ``Emission``
records. Anything the parser is unsure about becomes a ``ClarificationQuestion``
the client answers before commit — this is what keeps bad data out of the ledger.

Nothing here touches the emissions ledger until ``POST /ingest/{id}/commit`` runs
the confirmed rows through the real CalculationPipeline.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON


class IngestionStatus(str, Enum):
    """Lifecycle of an upload as it moves through the funnel."""

    UPLOADED = "uploaded"  # file received, not yet parsed
    ANALYZING = "analyzing"  # loader + mapper + grounding running
    NEEDS_ANSWERS = "needs_answers"  # clarifying questions await the client
    READY_FOR_REVIEW = "ready_for_review"  # all rows staged, awaiting human approve
    COMMITTING = "committing"  # writing approved rows to the ledger
    COMMITTED = "committed"  # done — Activities/Emissions created
    FAILED = "failed"  # unrecoverable error (see error_message)


class RowStatus(str, Enum):
    """Per-row review state the funnel sorts by."""

    NEEDS_QUESTION = "needs_question"  # blocked on a clarifying answer
    NEEDS_REVIEW = "needs_review"  # amber — human should eyeball it
    READY = "ready"  # green — mapped + grounded cleanly
    APPROVED = "approved"  # human confirmed → will commit
    REJECTED = "rejected"  # human discarded → will not commit
    COMMITTED = "committed"  # written to the ledger


class IngestionSession(SQLModel, table=True):
    """One uploaded file working through map → ground → rules → score → commit."""

    __tablename__ = "ingestion_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    reporting_period_id: Optional[UUID] = Field(
        default=None, foreign_key="reporting_periods.id", index=True
    )
    created_by: UUID = Field(foreign_key="users.id")

    # File info
    filename: str = Field(max_length=255)
    file_size_bytes: Optional[int] = Field(default=None)
    content_hash: Optional[str] = Field(default=None, max_length=64, index=True)

    status: IngestionStatus = Field(default=IngestionStatus.UPLOADED, index=True)

    # Rollup counts (kept in sync by the orchestrator for a cheap status poll)
    total_rows: int = Field(default=0)
    mapped_rows: int = Field(default=0)
    question_count: int = Field(default=0)
    open_question_count: int = Field(default=0)
    committed_count: int = Field(default=0)

    # Per-sheet / per-scope breakdown for the review header
    summary: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    error_message: Optional[str] = Field(default=None, max_length=1000)

    # Set once committed — ties staged rows back to a real ImportBatch
    import_batch_id: Optional[UUID] = Field(
        default=None, foreign_key="import_batches.id", index=True
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    staged_rows: list["StagedRow"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    questions: list["ClarificationQuestion"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class StagedRow(SQLModel, table=True):
    """A single source row after mapping/grounding/scoring, awaiting human review.

    ``source`` keeps the original row verbatim so the client always sees exactly
    what they uploaded next to what we inferred. ``scope``/``category_code`` come
    from the resolved catalog entry (never the LLM) so they're always consistent
    with the real emission factor.
    """

    __tablename__ = "staged_rows"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="ingestion_sessions.id", index=True)

    # Provenance back to the uploaded file
    sheet: str = Field(default="", max_length=255)
    row_index: int = Field(default=0)
    source: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # What the parser inferred
    activity_key: Optional[str] = Field(default=None, max_length=100, index=True)
    scope: Optional[int] = Field(default=None)
    category_code: Optional[str] = Field(default=None, max_length=10)
    quantity: Optional[float] = Field(default=None)
    unit: Optional[str] = Field(default=None, max_length=50)
    description: str = Field(default="", max_length=500)

    # Confidence + review state
    confidence: float = Field(default=0.0)
    band: str = Field(default="red", max_length=10)  # green | amber | red
    status: RowStatus = Field(default=RowStatus.NEEDS_REVIEW, index=True)
    pcaf_data_quality: Optional[int] = Field(default=None)
    # Data-quality ladder: measured | calculated | estimated | gap (the spine of the
    # inventory — what we can stand behind vs what's an estimate vs a gap).
    measurement_tier: Optional[str] = Field(default=None, max_length=12, index=True)
    reasons: Optional[list] = Field(default=None, sa_column=Column(JSON))

    # Set on commit — links to the real Activity created from this row
    committed_activity_id: Optional[UUID] = Field(
        default=None, foreign_key="activities.id"
    )
    commit_error: Optional[str] = Field(default=None, max_length=500)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    session: IngestionSession = Relationship(back_populates="staged_rows")
    questions: list["ClarificationQuestion"] = Relationship(back_populates="staged_row")


class ClarificationQuestion(SQLModel, table=True):
    """A targeted question the parser asks before it will trust a row.

    Examples: "Is this paper virgin or recycled?", "Commuting distance — one-way
    or round-trip?", "This gas figure is in m³ but the factor expects kWh — which
    did you mean?". Answering re-runs grounding/scoring for the linked row.
    """

    __tablename__ = "clarification_questions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="ingestion_sessions.id", index=True)
    staged_row_id: Optional[UUID] = Field(
        default=None, foreign_key="staged_rows.id", index=True
    )

    question: str = Field(max_length=1000)
    # Optional machine hint for the funnel to render the right control
    field: Optional[str] = Field(
        default=None, max_length=50
    )  # unit | activity | quantity | scope
    choices: Optional[list] = Field(default=None, sa_column=Column(JSON))

    answer: Optional[str] = Field(default=None, max_length=1000)
    answered: bool = Field(default=False, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    answered_at: Optional[datetime] = Field(default=None)

    # Relationships
    session: IngestionSession = Relationship(back_populates="questions")
    staged_row: Optional[StagedRow] = Relationship(back_populates="questions")
