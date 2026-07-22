"""Sample data endpoints — the "Load sample data" button.

Seeds the caller's own org with the flagged Galil Steel demo dataset
(activities → dashboard/report + target/scenarios) and removes it again in
one click. Everything created here carries is_demo=True; DELETE removes
exactly that set and never touches the user's real data.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User
from app.services.sample_data import SampleDataAlreadyLoaded, SampleDataService

router = APIRouter(prefix="/sample-data", tags=["Sample Data"])


class SampleDataStatusResponse(BaseModel):
    loaded: bool
    period_id: str | None
    activities: int


class SampleDataLoadResponse(BaseModel):
    period_id: str
    site_id: str
    activities_created: int
    rows_skipped: int
    total_co2e_tonnes: float
    target_created: bool
    scenarios_created: int
    products_created: int
    epd_created: bool
    cbam_imports_created: int


class SampleDataRemoveResponse(BaseModel):
    removed_activities: int
    removed_scenarios: int
    removed_targets: int
    removed_products: int
    removed_cbam_imports: int
    period_removed: bool
    periods_kept: int


@router.get("", response_model=SampleDataStatusResponse)
async def sample_data_status(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Whether this org currently has the sample dataset loaded."""
    return await SampleDataService.status(session, current_user.organization_id)


@router.post("", response_model=SampleDataLoadResponse)
async def load_sample_data(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Seed the org with the sample dataset (site, period, activities,
    target + scenarios). Refuses to double-load."""
    try:
        return await SampleDataService.load(session, current_user)
    except SampleDataAlreadyLoaded:
        raise HTTPException(
            status_code=409,
            detail="Sample data is already loaded. Remove it before loading again.",
        )


@router.delete("", response_model=SampleDataRemoveResponse)
async def remove_sample_data(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Remove every sample record from the org (activities, emissions,
    scenarios, target, and the sample site/period when nothing else uses
    them)."""
    return await SampleDataService.remove(session, current_user.organization_id)
