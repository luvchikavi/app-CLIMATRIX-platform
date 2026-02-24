"""
Activities API endpoints.

THIN CONTROLLER - Only handles HTTP concerns:
- Request parsing
- Response formatting
- Authentication
- Error translation

Business logic delegated to CalculationPipeline service.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User, ReportingPeriod, Organization
from app.models.emission import Activity, Emission, EmissionFactor, ConfidenceLevel, DataSource
from app.services.calculation import CalculationPipeline, ActivityInput
from app.services.calculation.pipeline import CalculationError
from app.services.calculation.resolver import FactorNotFoundError
from app.services.calculation.normalizer import UnitConversionError

router = APIRouter()


# ============================================================================
# Schemas (HTTP layer only)
# ============================================================================

class ActivityCreate(BaseModel):
    """Create activity request."""
    scope: int
    category_code: str
    activity_key: str
    description: str
    quantity: Decimal
    unit: str
    activity_date: date
    site_id: str | None = None
    # For Supplier-Specific method (3.1, 3.2): user provides their own emission factor
    supplier_ef: Decimal | None = None
    # Data quality fields (PCAF: 1=best, 5=worst)
    data_quality_score: int = 5  # Default to most conservative
    data_quality_justification: str | None = None
    supporting_document_url: str | None = None


class ActivityResponse(BaseModel):
    """Activity response."""
    id: str
    scope: int
    category_code: str
    activity_key: str
    description: str
    quantity: float
    unit: str
    activity_date: date
    site_id: str | None
    created_at: datetime
    data_source: str | None = None
    import_batch_id: str | None = None
    # Data quality fields
    data_quality_score: int = 5
    data_quality_justification: str | None = None
    supporting_document_url: str | None = None


class EmissionResponse(BaseModel):
    """Emission calculation response."""
    id: str
    activity_id: str
    co2e_kg: float
    co2_kg: float | None
    ch4_kg: float | None
    n2o_kg: float | None
    wtt_co2e_kg: float | None
    formula: str | None
    confidence: str
    resolution_strategy: str
    factor_used: str
    factor_source: str
    factor_value: float | None = None
    factor_unit: str | None = None
    warnings: list[str] = []
    # Calculation metadata (Phase 9B)
    factor_year: int | None = None
    factor_region: str | None = None
    method_hierarchy: str | None = None


class ActivityWithEmissionResponse(BaseModel):
    """Activity with its emission calculation."""
    activity: ActivityResponse
    emission: EmissionResponse | None


# ============================================================================
# Endpoints (HTTP handling only - business logic in services)
# ============================================================================

@router.get("/periods/{period_id}/activities", response_model=list[ActivityWithEmissionResponse])
async def list_activities(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    scope: int | None = None,
    category_code: str | None = None,
):
    """List all activities for a reporting period."""
    # Verify period belongs to organization
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    if not period_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Get activities
    query = select(Activity).where(
        Activity.reporting_period_id == period_id,
        Activity.organization_id == current_user.organization_id,
    )
    if scope:
        query = query.where(Activity.scope == scope)
    if category_code:
        query = query.where(Activity.category_code == category_code)

    result = await session.execute(query)
    activities = result.scalars().all()

    responses = []
    for a in activities:
        emission_query = select(Emission).where(Emission.activity_id == a.id)
        emission_result = await session.execute(emission_query)
        emission = emission_result.scalar_one_or_none()

        emission_response = None
        if emission:
            factor_query = select(EmissionFactor).where(EmissionFactor.id == emission.emission_factor_id)
            factor_result = await session.execute(factor_query)
            factor = factor_result.scalar_one_or_none()

            emission_response = EmissionResponse(
                id=str(emission.id),
                activity_id=str(emission.activity_id),
                co2e_kg=float(emission.co2e_kg),
                co2_kg=float(emission.co2_kg) if emission.co2_kg else None,
                ch4_kg=float(emission.ch4_kg) if emission.ch4_kg else None,
                n2o_kg=float(emission.n2o_kg) if emission.n2o_kg else None,
                wtt_co2e_kg=float(emission.wtt_co2e_kg) if emission.wtt_co2e_kg else None,
                formula=emission.formula,
                confidence=emission.confidence.value,
                resolution_strategy=emission.resolution_strategy or "exact",
                factor_used=factor.display_name if factor else "Unknown",
                factor_source=factor.source if factor else "Unknown",
                factor_value=float(factor.co2e_factor) if factor and factor.co2e_factor else None,
                factor_unit=factor.factor_unit if factor else None,
                warnings=[],
                # Calculation metadata (Phase 9B)
                factor_year=emission.factor_year,
                factor_region=emission.factor_region,
                method_hierarchy=emission.method_hierarchy,
            )

        responses.append(ActivityWithEmissionResponse(
            activity=ActivityResponse(
                id=str(a.id),
                scope=a.scope,
                category_code=a.category_code,
                activity_key=a.activity_key,
                description=a.description,
                quantity=float(a.quantity),
                unit=a.unit,
                activity_date=a.activity_date,
                site_id=str(a.site_id) if a.site_id else None,
                created_at=a.created_at,
                data_source=a.data_source.value if a.data_source else None,
                import_batch_id=str(a.import_batch_id) if a.import_batch_id else None,
                data_quality_score=a.data_quality_score if hasattr(a, 'data_quality_score') else 5,
                data_quality_justification=a.data_quality_justification if hasattr(a, 'data_quality_justification') else None,
                supporting_document_url=a.supporting_document_url if hasattr(a, 'supporting_document_url') else None,
            ),
            emission=emission_response,
        ))

    return responses


@router.post("/periods/{period_id}/activities", response_model=ActivityWithEmissionResponse)
async def create_activity(
    period_id: UUID,
    data: ActivityCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Create a new activity and calculate its emissions.

    Business logic delegated to CalculationPipeline:
    1. Unit normalization (Pint)
    2. Factor resolution (with region fallback)
    3. Emission calculation (strategy pattern)
    """
    # --- HTTP CONCERN: Validate period access ---
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    period = period_result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")
    if period.is_locked:
        raise HTTPException(status_code=400, detail="Cannot add activities to locked period")

    # Get organization's region for factor resolution
    org_query = select(Organization).where(Organization.id == current_user.organization_id)
    org_result = await session.execute(org_query)
    org = org_result.scalar_one_or_none()
    org_region = org.default_region if org and org.default_region else "Global"

    # --- BUSINESS LOGIC: Delegated to CalculationPipeline ---
    pipeline = CalculationPipeline(session)

    try:
        calc_result = await pipeline.calculate(ActivityInput(
            activity_key=data.activity_key,
            quantity=data.quantity,
            unit=data.unit,
            scope=data.scope,
            category_code=data.category_code,
            region=org_region,  # Use organization's configured region
            year=2024,
            supplier_ef=data.supplier_ef,  # For Supplier-Specific method
        ))
    except FactorNotFoundError as e:
        raise HTTPException(
            status_code=400,
            detail=f"No emission factor found for activity_key='{data.activity_key}'. "
                   f"Please select a valid activity type from the dropdown.",
        )
    except UnitConversionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CalculationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # --- HTTP CONCERN: Persist to database ---
    activity = Activity(
        organization_id=current_user.organization_id,
        reporting_period_id=period_id,
        scope=data.scope,
        category_code=data.category_code,
        activity_key=data.activity_key,
        description=data.description,
        quantity=data.quantity,
        unit=data.unit,
        activity_date=data.activity_date,
        site_id=UUID(data.site_id) if data.site_id else None,
        created_by=current_user.id,
        data_source=DataSource.MANUAL,
        # Data quality fields
        data_quality_score=data.data_quality_score,
        data_quality_justification=data.data_quality_justification,
        supporting_document_url=data.supporting_document_url,
    )
    session.add(activity)
    await session.flush()

    emission = Emission(
        activity_id=activity.id,
        emission_factor_id=calc_result.emission_factor_id,
        co2e_kg=calc_result.co2e_kg,
        co2_kg=calc_result.co2_kg,
        ch4_kg=calc_result.ch4_kg,
        n2o_kg=calc_result.n2o_kg,
        wtt_co2e_kg=calc_result.wtt_co2e_kg,
        converted_quantity=calc_result.converted_quantity,
        converted_unit=calc_result.converted_unit,
        formula=calc_result.formula,
        confidence=ConfidenceLevel(calc_result.confidence),
        resolution_strategy=calc_result.resolution_strategy,
        # Calculation metadata (Phase 9B)
        factor_year=calc_result.factor_year,
        factor_region=calc_result.factor_region,
        method_hierarchy=calc_result.method_hierarchy,
    )
    session.add(emission)
    await session.commit()
    await session.refresh(activity)
    await session.refresh(emission)

    # --- HTTP CONCERN: Format response ---
    return ActivityWithEmissionResponse(
        activity=ActivityResponse(
            id=str(activity.id),
            scope=activity.scope,
            category_code=activity.category_code,
            activity_key=activity.activity_key,
            description=activity.description,
            quantity=float(activity.quantity),
            unit=activity.unit,
            activity_date=activity.activity_date,
            site_id=str(activity.site_id) if activity.site_id else None,
            created_at=activity.created_at,
            data_source=activity.data_source.value if activity.data_source else None,
            import_batch_id=str(activity.import_batch_id) if activity.import_batch_id else None,
            data_quality_score=activity.data_quality_score,
            data_quality_justification=activity.data_quality_justification,
            supporting_document_url=activity.supporting_document_url,
        ),
        emission=EmissionResponse(
            id=str(emission.id),
            activity_id=str(emission.activity_id),
            co2e_kg=float(emission.co2e_kg),
            co2_kg=float(emission.co2_kg) if emission.co2_kg else None,
            ch4_kg=float(emission.ch4_kg) if emission.ch4_kg else None,
            n2o_kg=float(emission.n2o_kg) if emission.n2o_kg else None,
            wtt_co2e_kg=float(emission.wtt_co2e_kg) if emission.wtt_co2e_kg else None,
            formula=emission.formula,
            confidence=emission.confidence.value,
            resolution_strategy=emission.resolution_strategy or "exact",
            factor_used=calc_result.factor_display_name,
            factor_source=calc_result.factor_source,
            factor_value=float(calc_result.factor_value) if calc_result.factor_value else None,
            factor_unit=calc_result.factor_unit,
            warnings=calc_result.warnings,
            # Calculation metadata (Phase 9B)
            factor_year=calc_result.factor_year,
            factor_region=calc_result.factor_region,
            method_hierarchy=calc_result.method_hierarchy,
        ),
    )


@router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete an activity and its emission."""
    query = select(Activity).where(
        Activity.id == activity_id,
        Activity.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    emission_query = select(Emission).where(Emission.activity_id == activity_id)
    emission_result = await session.execute(emission_query)
    emission = emission_result.scalar_one_or_none()
    if emission:
        await session.delete(emission)

    await session.delete(activity)
    await session.commit()

    return {"status": "deleted", "id": str(activity_id)}


class RecalculateResponse(BaseModel):
    """Response for bulk recalculation."""
    total_activities: int
    recalculated: int
    failed: int
    errors: list[dict] = []


@router.post("/periods/{period_id}/emissions/recalculate", response_model=RecalculateResponse)
async def recalculate_period_emissions(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Recalculate all emissions for a reporting period.

    Useful when:
    - Emission factors have been updated
    - You want to refresh calculations with latest factors
    - WTT mappings have been added/updated

    This will re-run the calculation pipeline for every activity
    and update all emission records.
    """
    # Verify period belongs to organization
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    period = period_result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Get organization's region for factor resolution
    org_query = select(Organization).where(Organization.id == current_user.organization_id)
    org_result = await session.execute(org_query)
    org = org_result.scalar_one_or_none()
    org_region = org.default_region if org and org.default_region else "Global"

    # Get all activities for this period
    activities_query = select(Activity).where(
        Activity.reporting_period_id == period_id,
        Activity.organization_id == current_user.organization_id,
    )
    activities_result = await session.execute(activities_query)
    activities = activities_result.scalars().all()

    pipeline = CalculationPipeline(session)
    recalculated = 0
    failed = 0
    errors = []

    for activity in activities:
        try:
            # Recalculate using pipeline
            calc_result = await pipeline.calculate(ActivityInput(
                activity_key=activity.activity_key,
                quantity=activity.quantity,
                unit=activity.unit,
                scope=activity.scope,
                category_code=activity.category_code,
                region=org_region,  # Use organization's configured region
                year=2024,
            ))

            # Update existing emission or create new one
            emission_query = select(Emission).where(Emission.activity_id == activity.id)
            emission_result = await session.execute(emission_query)
            emission = emission_result.scalar_one_or_none()

            if emission:
                # Update existing
                emission.emission_factor_id = calc_result.emission_factor_id
                emission.co2e_kg = calc_result.co2e_kg
                emission.co2_kg = calc_result.co2_kg
                emission.ch4_kg = calc_result.ch4_kg
                emission.n2o_kg = calc_result.n2o_kg
                emission.wtt_co2e_kg = calc_result.wtt_co2e_kg
                emission.converted_quantity = calc_result.converted_quantity
                emission.converted_unit = calc_result.converted_unit
                emission.formula = calc_result.formula
                emission.confidence = ConfidenceLevel(calc_result.confidence)
                emission.resolution_strategy = calc_result.resolution_strategy
                emission.recalculated_at = datetime.utcnow()
                # Calculation metadata (Phase 9B)
                emission.factor_year = calc_result.factor_year
                emission.factor_region = calc_result.factor_region
                emission.method_hierarchy = calc_result.method_hierarchy
            else:
                # Create new emission
                emission = Emission(
                    activity_id=activity.id,
                    emission_factor_id=calc_result.emission_factor_id,
                    co2e_kg=calc_result.co2e_kg,
                    co2_kg=calc_result.co2_kg,
                    ch4_kg=calc_result.ch4_kg,
                    n2o_kg=calc_result.n2o_kg,
                    wtt_co2e_kg=calc_result.wtt_co2e_kg,
                    converted_quantity=calc_result.converted_quantity,
                    converted_unit=calc_result.converted_unit,
                    formula=calc_result.formula,
                    confidence=ConfidenceLevel(calc_result.confidence),
                    resolution_strategy=calc_result.resolution_strategy,
                    # Calculation metadata (Phase 9B)
                    factor_year=calc_result.factor_year,
                    factor_region=calc_result.factor_region,
                    method_hierarchy=calc_result.method_hierarchy,
                )
                session.add(emission)

            recalculated += 1

        except Exception as e:
            failed += 1
            errors.append({
                "activity_id": str(activity.id),
                "activity_key": activity.activity_key,
                "error": str(e),
            })

    await session.commit()

    return RecalculateResponse(
        total_activities=len(activities),
        recalculated=recalculated,
        failed=failed,
        errors=errors,
    )


# ============================================================================
# Bulk Delete Endpoints
# ============================================================================

class BulkDeleteResponse(BaseModel):
    """Response for bulk delete operations."""
    deleted_activities: int
    deleted_emissions: int
    message: str


@router.delete("/periods/{period_id}/activities", response_model=BulkDeleteResponse)
async def delete_period_activities(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Delete ALL activities for a reporting period.

    This is a destructive operation - use with caution.
    Useful for clearing data before re-importing.

    Also deletes all associated emissions and clears import batch references.
    """
    from sqlmodel import delete

    # Verify period belongs to organization
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    period = period_result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    if period.is_locked:
        raise HTTPException(status_code=400, detail="Cannot delete activities from locked period")

    # Get activity IDs for this period
    activities_query = select(Activity.id).where(
        Activity.reporting_period_id == period_id,
        Activity.organization_id == current_user.organization_id,
    )
    activities_result = await session.execute(activities_query)
    activity_ids = [a for a in activities_result.scalars().all()]

    deleted_emissions = 0
    deleted_activities = 0

    if activity_ids:
        # Delete emissions first (FK constraint)
        emissions_delete = await session.execute(
            delete(Emission).where(Emission.activity_id.in_(activity_ids))
        )
        deleted_emissions = emissions_delete.rowcount

        # Delete activities
        activities_delete = await session.execute(
            delete(Activity).where(
                Activity.reporting_period_id == period_id,
                Activity.organization_id == current_user.organization_id,
            )
        )
        deleted_activities = activities_delete.rowcount

    # Also delete import batches for this period
    from app.models.emission import ImportBatch
    await session.execute(
        delete(ImportBatch).where(
            ImportBatch.reporting_period_id == period_id,
            ImportBatch.organization_id == current_user.organization_id,
        )
    )

    await session.commit()

    return BulkDeleteResponse(
        deleted_activities=deleted_activities,
        deleted_emissions=deleted_emissions,
        message=f"Successfully deleted {deleted_activities} activities and {deleted_emissions} emissions from period",
    )


@router.delete("/organization/activities", response_model=BulkDeleteResponse)
async def delete_organization_activities(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    confirm: bool = False,
):
    """
    Delete ALL activities for the organization across ALL periods.

    This is a VERY destructive operation - requires confirm=true parameter.
    Useful for completely resetting an organization's data.

    Also deletes all associated emissions and import batches.
    """
    from sqlmodel import delete

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="This will delete ALL data for your organization. "
                   "Pass confirm=true to proceed."
        )

    # Get all activity IDs for the organization
    activities_query = select(Activity.id).where(
        Activity.organization_id == current_user.organization_id,
    )
    activities_result = await session.execute(activities_query)
    activity_ids = [a for a in activities_result.scalars().all()]

    deleted_emissions = 0
    deleted_activities = 0

    if activity_ids:
        # Delete emissions first (FK constraint)
        emissions_delete = await session.execute(
            delete(Emission).where(Emission.activity_id.in_(activity_ids))
        )
        deleted_emissions = emissions_delete.rowcount

        # Delete all activities for organization
        activities_delete = await session.execute(
            delete(Activity).where(
                Activity.organization_id == current_user.organization_id,
            )
        )
        deleted_activities = activities_delete.rowcount

    # Delete all import batches for organization
    from app.models.emission import ImportBatch
    await session.execute(
        delete(ImportBatch).where(
            ImportBatch.organization_id == current_user.organization_id,
        )
    )

    await session.commit()

    return BulkDeleteResponse(
        deleted_activities=deleted_activities,
        deleted_emissions=deleted_emissions,
        message=f"Successfully deleted ALL data: {deleted_activities} activities and {deleted_emissions} emissions",
    )
