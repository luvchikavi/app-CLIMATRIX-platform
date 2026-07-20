"""FK ondelete rules for the ingestion chain — user deletes must not 500.

Deleting an imported Activity, an ImportBatch or a ReportingPeriod previously
hit bare FK constraints from staged_rows.committed_activity_id and
ingestion_sessions.{import_batch_id,reporting_period_id} (no ondelete), which
raises IntegrityError -> 500 on Postgres for every Smart-Import user. The
staging/audit rows must survive the delete with the reference nulled, so all
three become ON DELETE SET NULL.

SQLite (dev/tests) doesn't enforce these FKs and tables come from create_all —
the migration is a Postgres-only change.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-07-20
"""

from alembic import op

revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None

_FKS = [
    ("staged_rows", "committed_activity_id", "activities"),
    ("ingestion_sessions", "import_batch_id", "import_batches"),
    ("ingestion_sessions", "reporting_period_id", "reporting_periods"),
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    # Constraint names come from create_all-era defaults; drop whatever FK
    # exists on each column by catalog lookup rather than guessing the name.
    for table, column, reftable in _FKS:
        op.execute(f"""
            DO $$
            DECLARE r record;
            BEGIN
              FOR r IN
                SELECT con.conname
                FROM pg_constraint con
                JOIN pg_attribute att
                  ON att.attrelid = con.conrelid
                 AND att.attnum = ANY (con.conkey)
                WHERE con.contype = 'f'
                  AND con.conrelid = '{table}'::regclass
                  AND att.attname = '{column}'
              LOOP
                EXECUTE format('ALTER TABLE {table} DROP CONSTRAINT %I', r.conname);
              END LOOP;
            END $$;
            """)
        op.create_foreign_key(
            f"{table}_{column}_fkey",
            table,
            reftable,
            [column],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table, column, reftable in _FKS:
        op.drop_constraint(f"{table}_{column}_fkey", table, type_="foreignkey")
        op.create_foreign_key(
            f"{table}_{column}_fkey", table, reftable, [column], ["id"]
        )
