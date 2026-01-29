#!/usr/bin/env python
"""
Script to seed the initiatives library.
Run from backend directory: python scripts/seed_initiatives.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.seeds.initiatives import seed_initiatives


async def main():
    """Seed the initiatives library."""
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        count = await seed_initiatives(session)
        if count > 0:
            print(f"Successfully seeded {count} initiatives.")
        else:
            print("Initiatives already exist. Skipping seed.")


if __name__ == "__main__":
    asyncio.run(main())
