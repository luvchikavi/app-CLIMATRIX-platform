"""add ingestion staging tables (the drop-any-file funnel)

Revision ID: c1d2e3f4a5b6
Revises: bd6bedf13533
Create Date: 2026-07-06 02:10:00.000000

Adds the staging layer that sits in front of the emissions ledger:
  - ingestion_sessions   : one uploaded file working through the parser
  - staged_rows          : each source row mapped/grounded/scored, pre-commit
  - clarification_questions : targeted questions the client answers before commit

Nothing here mutates activities/emissions — commit happens via the API endpoint
that runs approved staged rows through the real CalculationPipeline.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "bd6bedf13533"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- ingestion_sessions -------------------------------------------------
    op.create_table(
        "ingestion_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("reporting_period_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "filename", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column(
            "content_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True
        ),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("mapped_rows", sa.Integer(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("open_question_count", sa.Integer(), nullable=False),
        sa.Column("committed_count", sa.Integer(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column(
            "error_message",
            sqlmodel.sql.sqltypes.AutoString(length=1000),
            nullable=True,
        ),
        sa.Column("import_batch_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reporting_period_id"],
            ["reporting_periods.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["import_batch_id"],
            ["import_batches.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ingestion_sessions_organization_id"),
        "ingestion_sessions",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_sessions_reporting_period_id"),
        "ingestion_sessions",
        ["reporting_period_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_sessions_content_hash"),
        "ingestion_sessions",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_sessions_status"),
        "ingestion_sessions",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_sessions_import_batch_id"),
        "ingestion_sessions",
        ["import_batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_sessions_created_at"),
        "ingestion_sessions",
        ["created_at"],
        unique=False,
    )

    # ---- staged_rows --------------------------------------------------------
    op.create_table(
        "staged_rows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column(
            "sheet", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("source", sa.JSON(), nullable=True),
        sa.Column(
            "activity_key", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True
        ),
        sa.Column("scope", sa.Integer(), nullable=True),
        sa.Column(
            "category_code", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=True
        ),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column(
            "description", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("band", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("pcaf_data_quality", sa.Integer(), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("committed_activity_id", sa.Uuid(), nullable=True),
        sa.Column(
            "commit_error", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["ingestion_sessions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["committed_activity_id"],
            ["activities.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_staged_rows_session_id"), "staged_rows", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_staged_rows_activity_key"),
        "staged_rows",
        ["activity_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_staged_rows_status"), "staged_rows", ["status"], unique=False
    )

    # ---- clarification_questions -------------------------------------------
    op.create_table(
        "clarification_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("staged_row_id", sa.Uuid(), nullable=True),
        sa.Column(
            "question", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False
        ),
        sa.Column("field", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("choices", sa.JSON(), nullable=True),
        sa.Column(
            "answer", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True
        ),
        sa.Column("answered", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("answered_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["ingestion_sessions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["staged_row_id"],
            ["staged_rows.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_clarification_questions_session_id"),
        "clarification_questions",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clarification_questions_staged_row_id"),
        "clarification_questions",
        ["staged_row_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clarification_questions_answered"),
        "clarification_questions",
        ["answered"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_clarification_questions_answered"),
        table_name="clarification_questions",
    )
    op.drop_index(
        op.f("ix_clarification_questions_staged_row_id"),
        table_name="clarification_questions",
    )
    op.drop_index(
        op.f("ix_clarification_questions_session_id"),
        table_name="clarification_questions",
    )
    op.drop_table("clarification_questions")
    op.drop_index(op.f("ix_staged_rows_status"), table_name="staged_rows")
    op.drop_index(op.f("ix_staged_rows_activity_key"), table_name="staged_rows")
    op.drop_index(op.f("ix_staged_rows_session_id"), table_name="staged_rows")
    op.drop_table("staged_rows")
    op.drop_index(
        op.f("ix_ingestion_sessions_created_at"), table_name="ingestion_sessions"
    )
    op.drop_index(
        op.f("ix_ingestion_sessions_import_batch_id"), table_name="ingestion_sessions"
    )
    op.drop_index(op.f("ix_ingestion_sessions_status"), table_name="ingestion_sessions")
    op.drop_index(
        op.f("ix_ingestion_sessions_content_hash"), table_name="ingestion_sessions"
    )
    op.drop_index(
        op.f("ix_ingestion_sessions_reporting_period_id"),
        table_name="ingestion_sessions",
    )
    op.drop_index(
        op.f("ix_ingestion_sessions_organization_id"), table_name="ingestion_sessions"
    )
    op.drop_table("ingestion_sessions")
