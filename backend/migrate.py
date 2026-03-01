"""
Pre-migration script for Railway deployment.

Checks if the database has an Alembic revision stamped. If not (tables exist
but no alembic_version row), stamps at the comprehensive baseline so that
`alembic upgrade head` can run the incremental migrations.

Uses information_schema queries to avoid failed SELECTs that abort PostgreSQL
transactions.
"""
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


async def ensure_stamped() -> None:
    engine = create_async_engine(settings.async_database_url)
    try:
        async with engine.connect() as conn:
            # Check if alembic_version table exists (no failed queries = no aborted txn)
            result = await conn.execute(text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_name = 'alembic_version'"
                ")"
            ))
            has_alembic_table = result.scalar()

            if has_alembic_table:
                result = await conn.execute(text(
                    "SELECT version_num FROM alembic_version LIMIT 1"
                ))
                row = result.first()
                if row:
                    print(f"[migrate] Alembic already at revision: {row[0]}")
                    return
                # Table exists but empty — fall through to stamp

            # Check if actual data tables exist (DB was created outside Alembic)
            result = await conn.execute(text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_name = 'emission_factors'"
                ")"
            ))
            has_tables = result.scalar()

            if has_tables:
                print("[migrate] Tables exist but no Alembic revision. Stamping baseline...")
                await conn.execute(text(
                    "CREATE TABLE IF NOT EXISTS alembic_version "
                    "(version_num VARCHAR(32) NOT NULL)"
                ))
                await conn.execute(text(
                    "INSERT INTO alembic_version (version_num) VALUES ('f1a2b3c4d5e6')"
                ))
                await conn.commit()
                print("[migrate] Stamped at f1a2b3c4d5e6 (comprehensive baseline)")
            else:
                print("[migrate] Fresh database — alembic upgrade will handle everything")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(ensure_stamped())
