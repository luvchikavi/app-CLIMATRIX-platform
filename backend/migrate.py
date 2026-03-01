"""
Pre-migration script for Railway deployment.

Checks if the database has an Alembic revision stamped. If not (tables exist
but no alembic_version row), stamps at the comprehensive baseline so that
`alembic upgrade head` can run the incremental migrations.
"""
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


async def ensure_stamped() -> None:
    engine = create_async_engine(settings.async_database_url)
    try:
        async with engine.connect() as conn:
            # Check if alembic_version table exists and has a row
            try:
                result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                row = result.first()
                if row:
                    print(f"[migrate] Alembic already at revision: {row[0]}")
                    return
            except Exception:
                pass  # Table doesn't exist yet — alembic upgrade will create it

            # Check if actual data tables exist (DB was created outside Alembic)
            try:
                await conn.execute(text("SELECT 1 FROM emission_factors LIMIT 1"))
                has_tables = True
            except Exception:
                has_tables = False

            if has_tables:
                print("[migrate] Tables exist but no Alembic revision. Stamping baseline...")
                # Create alembic_version table and insert baseline stamp
                await conn.execute(text(
                    "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"
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
