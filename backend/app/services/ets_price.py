"""
EU ETS price fetch job.

CBAM certificate prices are based on EU ETS auction averages (quarterly
averages for 2026 emissions, weekly averages from 2027). This service keeps
the `eu_ets_prices` table fresh.

Public-source status (researched 2026-07-09):
- api.energy-charts.info exposes electricity/market endpoints only — no
  EUA/CO2 price endpoint.
- Ember's API (api.ember-energy.org) covers power-sector data and requires
  an API key; no free keyless EUA spot/auction price endpoint.
- ICAP's Allowance Price Explorer has no stable public JSON endpoint.
- Commercial APIs (OilPriceAPI etc.) require paid keys.

Conclusion: there is currently NO reliable free keyless endpoint for the EU
ETS price, so `fetch_latest()` uses a clearly-named placeholder source that
returns None. The admin manual path is `PUT /api/cbam/ets-price`
(admin/super_admin), which upserts a weekly price row; consumers (screening,
screen-defaults) fall back to €75/tCO2e with an explicit assumption string
when the table is empty.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.cbam import EUETSPrice

logger = logging.getLogger(__name__)

# Fallback used by consumers when no price row exists in the DB.
FALLBACK_ETS_PRICE_EUR = Decimal("75.0")
FALLBACK_ASSUMPTION = (
    "ETS price of €75/tCO2e is a placeholder pending the "
    "automated EU ETS price feed."
)


async def placeholder_public_source_fetch() -> Optional[dict]:
    """
    Placeholder for a public EU ETS price source.

    As of July 2026 no reliable free keyless API for the EUA price exists
    (energy-charts.info and Ember were evaluated — neither exposes one).
    Returns None, meaning "no live data available". Replace this function
    with a real fetcher (returning {"price_date": date, "price_eur":
    Decimal, "source": str, "source_url": str}) once a source is chosen.
    """
    return None


async def upsert_price(
    session: AsyncSession,
    price_date: date,
    price_eur: Decimal,
    source: str = "manual admin entry",
    source_url: Optional[str] = None,
) -> EUETSPrice:
    """Insert or update the EUETSPrice row for `price_date`."""
    result = await session.execute(
        select(EUETSPrice).where(EUETSPrice.price_date == price_date)
    )
    row = result.scalar_one_or_none()
    if row:
        row.price_eur = price_eur
        row.source = source
        row.source_url = source_url
    else:
        row = EUETSPrice(
            price_date=price_date,
            week_number=price_date.isocalendar()[1],
            year=price_date.year,
            price_eur=price_eur,
            source=source,
            source_url=source_url,
        )
        session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def fetch_latest(session: AsyncSession) -> Optional[EUETSPrice]:
    """
    Try to fetch the latest EU ETS price from a public source and upsert it.

    Returns the upserted EUETSPrice row, or None when no live source is
    available (the current state — see module docstring).
    """
    data = await placeholder_public_source_fetch()
    if data is None:
        logger.info(
            "ets_price.fetch_latest: no live public source configured; "
            "use PUT /api/cbam/ets-price for manual entry"
        )
        return None

    return await upsert_price(
        session,
        price_date=data["price_date"],
        price_eur=data["price_eur"],
        source=data.get("source", "public feed"),
        source_url=data.get("source_url"),
    )


async def get_latest_price(session: AsyncSession) -> Optional[EUETSPrice]:
    """Return the newest EUETSPrice row (by price_date), or None."""
    result = await session.execute(
        select(EUETSPrice).order_by(EUETSPrice.price_date.desc()).limit(1)
    )
    return result.scalars().first()
