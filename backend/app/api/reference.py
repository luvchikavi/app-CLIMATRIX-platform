"""
Reference Data API endpoints.
Provides emission factors, activity options, and unit information.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.emission import EmissionFactor, FuelPrice

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class EmissionFactorResponse(BaseModel):
    """Emission factor response."""
    id: str
    activity_key: str
    display_name: str
    scope: int
    category_code: str
    co2e_factor: float
    activity_unit: str
    factor_unit: str
    source: str
    region: str
    year: int


class ActivityOptionResponse(BaseModel):
    """Activity option for a category - includes emission factor for preview calculations."""
    id: str
    activity_key: str
    display_name: str
    unit: str
    scope: int
    category_code: str
    # Critical: Include emission factor data for frontend calculations
    co2e_factor: float
    factor_unit: str
    source: str
    region: str
    year: int


class UnitInfoResponse(BaseModel):
    """Unit information for an activity type."""
    activity_key: str
    expected_unit: str
    allowed_units: list[str]


# ============================================================================
# Helper Functions
# ============================================================================

def normalize_category_code(category_code: str) -> str:
    """
    Normalize category codes to match database values.

    Database stores emission factors with full subcategory codes (1.1, 1.2, 2.1, 2.2, etc.)
    so we pass through the category code as-is.

    Note: Previous implementation mapped 2.1/2.2/2.3 to "2" but this was incorrect
    since the database actually stores factors with the subcategory codes.
    """
    # Pass through as-is - database has subcategory codes (1.1, 1.2, 2.1, 2.2, etc.)
    return category_code


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/emission-factors", response_model=list[EmissionFactorResponse])
async def list_emission_factors(
    session: Annotated[AsyncSession, Depends(get_session)],
    scope: int | None = Query(None, ge=1, le=3),
    category_code: str | None = None,
    region: str | None = None,
    source: str | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
):
    """
    List emission factors with optional filters.

    Filters:
    - scope: Filter by GHG scope (1, 2, or 3)
    - category_code: Filter by category (e.g., "1.1", "3.5")
    - region: Filter by region (e.g., "UK", "US", "Global")
    - source: Filter by source (e.g., "DEFRA_2024")
    """
    query = select(EmissionFactor).where(EmissionFactor.is_active == True)

    if scope:
        query = query.where(EmissionFactor.scope == scope)
    if category_code:
        # Normalize category code for database lookup
        db_category_code = normalize_category_code(category_code)
        query = query.where(EmissionFactor.category_code == db_category_code)
    if region:
        query = query.where(EmissionFactor.region == region)
    if source:
        query = query.where(EmissionFactor.source == source)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    factors = result.scalars().all()

    return [
        EmissionFactorResponse(
            id=str(f.id),
            activity_key=f.activity_key,
            display_name=f.display_name,
            scope=f.scope,
            category_code=f.category_code,
            co2e_factor=float(f.co2e_factor),
            activity_unit=f.activity_unit,
            factor_unit=f.factor_unit,
            source=f.source,
            region=f.region,
            year=f.year,
        )
        for f in factors
    ]


@router.get("/emission-factors/{activity_key}", response_model=EmissionFactorResponse)
async def get_emission_factor(
    activity_key: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    region: str = "Global",
    year: int | None = None,
):
    """
    Get specific emission factor by activity_key.

    Resolution order:
    1. Exact match (activity_key + region + year)
    2. Region match (activity_key + region, latest year)
    3. Global fallback (activity_key + Global)
    """
    # Build query with region preference
    query = (
        select(EmissionFactor)
        .where(
            EmissionFactor.activity_key == activity_key,
            EmissionFactor.is_active == True,
        )
        .order_by(
            # Prefer exact region match, then Global
            EmissionFactor.region != region,
            EmissionFactor.year.desc(),
        )
    )

    if year:
        query = query.where(EmissionFactor.year == year)

    result = await session.execute(query)
    factor = result.scalar_one_or_none()

    if not factor:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"No emission factor found for activity_key='{activity_key}' in region='{region}'"
        )

    return EmissionFactorResponse(
        id=str(factor.id),
        activity_key=factor.activity_key,
        display_name=factor.display_name,
        scope=factor.scope,
        category_code=factor.category_code,
        co2e_factor=float(factor.co2e_factor),
        activity_unit=factor.activity_unit,
        factor_unit=factor.factor_unit,
        source=factor.source,
        region=factor.region,
        year=factor.year,
    )


@router.get("/activity-options/{category_code}", response_model=list[ActivityOptionResponse])
async def get_activity_options(
    category_code: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    region: str = "Global",
):
    """
    Get valid activity options for a category.

    This is the critical endpoint that populates the frontend dropdown.
    Frontend selects activity_key from these options, ensuring valid factor match.

    Note: Subcategory codes (2.1, 2.2, 2.3) are normalized to base codes for lookup.
    """
    # Normalize category code for database lookup
    db_category_code = normalize_category_code(category_code)

    query = (
        select(EmissionFactor)
        .where(
            EmissionFactor.category_code == db_category_code,
            EmissionFactor.is_active == True,
        )
        .distinct(EmissionFactor.activity_key)
    )

    result = await session.execute(query)
    factors = result.scalars().all()

    return [
        ActivityOptionResponse(
            id=str(f.id),
            activity_key=f.activity_key,
            display_name=f.display_name,
            unit=f.activity_unit,
            scope=f.scope,
            category_code=f.category_code,
            # Critical: Include emission factor data for frontend calculations
            co2e_factor=float(f.co2e_factor),
            factor_unit=f.factor_unit,
            source=f.source,
            region=f.region,
            year=f.year,
        )
        for f in factors
    ]


@router.get("/units/{activity_key}", response_model=UnitInfoResponse)
async def get_unit_info(
    activity_key: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Get unit information for an activity type.

    Returns the expected unit and any alternative units that can be converted.
    """
    query = (
        select(EmissionFactor)
        .where(
            EmissionFactor.activity_key == activity_key,
            EmissionFactor.is_active == True,
        )
        .limit(1)
    )

    result = await session.execute(query)
    factor = result.scalar_one_or_none()

    if not factor:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"No emission factor found for activity_key='{activity_key}'"
        )

    # Define allowed units per category
    # These can be converted using the UnitConversion table
    ALLOWED_UNITS = {
        "liters": ["liters", "L", "gallons", "gal"],
        "kWh": ["kWh", "MWh", "GWh"],
        "m3": ["m3", "cubic meters", "ft3", "cubic feet"],
        "kg": ["kg", "tonnes", "t", "lb", "lbs"],
        "km": ["km", "miles", "mi"],
        "USD": ["USD", "EUR", "GBP", "ILS"],
    }

    expected_unit = factor.activity_unit
    allowed_units = ALLOWED_UNITS.get(expected_unit, [expected_unit])

    return UnitInfoResponse(
        activity_key=activity_key,
        expected_unit=expected_unit,
        allowed_units=allowed_units,
    )


# ============================================================================
# Airport/Flight Distance Endpoints
# ============================================================================

class AirportResponse(BaseModel):
    """Airport information."""
    iata_code: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float


class FlightDistanceResponse(BaseModel):
    """Flight distance calculation result."""
    origin: AirportResponse
    destination: AirportResponse
    distance_km: float
    haul_type: str  # short, medium, long
    suggested_activity_key: str
    emission_factor_info: str


@router.get("/airports/search", response_model=list[AirportResponse])
async def search_airports(
    q: str = Query(..., min_length=2, description="Search term (IATA code, city, or airport name)"),
    limit: int = Query(10, le=50),
):
    """
    Search airports by IATA code, city name, or airport name.

    Examples:
    - GET /reference/airports/search?q=LON → London airports
    - GET /reference/airports/search?q=JFK → JFK airport
    - GET /reference/airports/search?q=Tel → Tel Aviv airport
    """
    from app.data import search_airports as do_search

    results = do_search(q, limit=limit)
    return [AirportResponse(**r) for r in results]


@router.get("/airports/stats")
async def get_airport_statistics():
    """
    Get statistics about the airport database coverage.
    """
    from app.data import get_airport_stats
    return get_airport_stats()


@router.get("/airports/{iata_code}", response_model=AirportResponse)
async def get_airport(iata_code: str):
    """
    Get airport details by IATA code.

    Example: GET /reference/airports/TLV → Ben Gurion Airport details
    """
    from app.data import get_airport as do_get_airport
    from fastapi import HTTPException

    airport_data = do_get_airport(iata_code)
    if not airport_data:
        raise HTTPException(
            status_code=404,
            detail=f"Airport not found: '{iata_code}'. Use /reference/airports/search to find valid codes."
        )

    name, city, country, lat, lon = airport_data
    return AirportResponse(
        iata_code=iata_code.upper(),
        name=name,
        city=city,
        country=country,
        latitude=lat,
        longitude=lon,
    )


@router.get("/flight-distance", response_model=FlightDistanceResponse)
async def calculate_flight_distance(
    origin: str = Query(..., min_length=3, max_length=3, description="Origin IATA code"),
    destination: str = Query(..., min_length=3, max_length=3, description="Destination IATA code"),
    cabin_class: str = Query("economy", description="Cabin class: economy, premium_economy, business, first"),
):
    """
    Calculate flight distance between two airports and suggest emission factor.

    Returns:
    - Great-circle distance in kilometers
    - Flight classification (short/medium/long haul)
    - Suggested activity_key for emission calculation

    Example: GET /reference/flight-distance?origin=TLV&destination=LHR
    """
    from app.data import (
        get_airport as do_get_airport,
        calculate_flight_distance as do_calc_distance,
        classify_flight_distance,
        get_flight_emission_key,
    )
    from fastapi import HTTPException

    origin_data = do_get_airport(origin)
    dest_data = do_get_airport(destination)

    if not origin_data:
        raise HTTPException(status_code=404, detail=f"Origin airport not found: '{origin}'")
    if not dest_data:
        raise HTTPException(status_code=404, detail=f"Destination airport not found: '{destination}'")

    distance = do_calc_distance(origin, destination)
    haul_type = classify_flight_distance(distance)
    activity_key = get_flight_emission_key(origin, destination, cabin_class)

    origin_name, origin_city, origin_country, origin_lat, origin_lon = origin_data
    dest_name, dest_city, dest_country, dest_lat, dest_lon = dest_data

    return FlightDistanceResponse(
        origin=AirportResponse(
            iata_code=origin.upper(),
            name=origin_name,
            city=origin_city,
            country=origin_country,
            latitude=origin_lat,
            longitude=origin_lon,
        ),
        destination=AirportResponse(
            iata_code=destination.upper(),
            name=dest_name,
            city=dest_city,
            country=dest_country,
            latitude=dest_lat,
            longitude=dest_lon,
        ),
        distance_km=round(distance, 1),
        haul_type=haul_type,
        suggested_activity_key=activity_key,
        emission_factor_info=f"Use activity_key='{activity_key}' with quantity={round(distance, 1)} km",
    )


# ============================================================================
# Fuel Price Endpoints (For Spend-to-Quantity Conversion)
# ============================================================================

class FuelPriceResponse(BaseModel):
    """Fuel price information."""
    id: str
    fuel_type: str
    price_per_unit: float
    currency: str
    unit: str
    region: str
    source: str
    source_url: str | None = None
    valid_from: str
    valid_until: str | None = None


class SpendConversionRequest(BaseModel):
    """Request for spend-to-quantity conversion."""
    fuel_type: str
    spend_amount: float
    currency: str
    region: str = "Global"


class SpendConversionResponse(BaseModel):
    """Result of spend-to-quantity conversion."""
    fuel_type: str
    spend_amount: float
    currency: str
    fuel_price: float
    price_unit: str
    price_source: str
    calculated_quantity: float
    quantity_unit: str
    formula: str


@router.get("/fuel-prices", response_model=list[FuelPriceResponse])
async def list_fuel_prices(
    session: Annotated[AsyncSession, Depends(get_session)],
    fuel_type: str | None = None,
    region: str | None = None,
    currency: str | None = None,
):
    """
    List available fuel prices.

    Used by frontend to show available options for spend-based calculations.

    Filters:
    - fuel_type: diesel, petrol, natural_gas, lpg, electricity, etc.
    - region: US, UK, IL, EU, Global
    - currency: USD, GBP, EUR, ILS
    """
    query = select(FuelPrice).where(FuelPrice.is_active == True)

    if fuel_type:
        query = query.where(FuelPrice.fuel_type == fuel_type)
    if region:
        query = query.where(FuelPrice.region == region)
    if currency:
        query = query.where(FuelPrice.currency == currency)

    query = query.order_by(FuelPrice.fuel_type, FuelPrice.region)
    result = await session.execute(query)
    prices = result.scalars().all()

    return [
        FuelPriceResponse(
            id=str(p.id),
            fuel_type=p.fuel_type,
            price_per_unit=float(p.price_per_unit),
            currency=p.currency,
            unit=p.unit,
            region=p.region,
            source=p.source,
            source_url=p.source_url,
            valid_from=str(p.valid_from),
            valid_until=str(p.valid_until) if p.valid_until else None,
        )
        for p in prices
    ]


@router.get("/fuel-prices/{fuel_type}", response_model=FuelPriceResponse)
async def get_fuel_price(
    fuel_type: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    region: str = "Global",
    currency: str | None = None,
):
    """
    Get fuel price for a specific fuel type and region.

    Resolution order:
    1. Exact match (fuel_type + region + currency)
    2. Region match (fuel_type + region)
    3. Global fallback (fuel_type + Global)

    Example: GET /reference/fuel-prices/diesel?region=IL
    """
    from fastapi import HTTPException

    # Build query with region preference
    query = (
        select(FuelPrice)
        .where(
            FuelPrice.fuel_type == fuel_type,
            FuelPrice.is_active == True,
        )
    )

    if currency:
        query = query.where(FuelPrice.currency == currency)

    # Order by region preference (exact match first, then Global)
    query = query.order_by(
        FuelPrice.region != region,  # False (0) for exact match, True (1) for others
        FuelPrice.valid_from.desc(),
    )

    result = await session.execute(query)
    price = result.scalar_one_or_none()

    if not price:
        raise HTTPException(
            status_code=404,
            detail=f"No fuel price found for fuel_type='{fuel_type}' in region='{region}'"
        )

    return FuelPriceResponse(
        id=str(price.id),
        fuel_type=price.fuel_type,
        price_per_unit=float(price.price_per_unit),
        currency=price.currency,
        unit=price.unit,
        region=price.region,
        source=price.source,
        source_url=price.source_url,
        valid_from=str(price.valid_from),
        valid_until=str(price.valid_until) if price.valid_until else None,
    )


@router.post("/convert-spend", response_model=SpendConversionResponse)
async def convert_spend_to_quantity(
    request: SpendConversionRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Convert monetary spend to physical quantity.

    This is used for Scope 1 calculations when user only has invoice data.

    Formula: quantity = spend_amount / price_per_unit

    Example:
    - Input: $5000 spent on diesel in US
    - Price: $1.00/liter (EIA 2024)
    - Output: 5000 liters

    Request body:
    ```json
    {
        "fuel_type": "diesel",
        "spend_amount": 5000,
        "currency": "USD",
        "region": "US"
    }
    ```
    """
    from fastapi import HTTPException

    # Get fuel price (prefer exact region match, then Global)
    query = (
        select(FuelPrice)
        .where(
            FuelPrice.fuel_type == request.fuel_type,
            FuelPrice.currency == request.currency,
            FuelPrice.is_active == True,
        )
        .order_by(
            FuelPrice.region != request.region,  # Exact match first
            FuelPrice.valid_from.desc(),
        )
        .limit(1)  # Get only the best match
    )

    result = await session.execute(query)
    price = result.scalar_one_or_none()

    if not price:
        raise HTTPException(
            status_code=404,
            detail=f"No fuel price found for {request.fuel_type} in {request.currency}. "
                   f"Available currencies can be found at GET /reference/fuel-prices?fuel_type={request.fuel_type}"
        )

    # Calculate quantity
    calculated_quantity = request.spend_amount / float(price.price_per_unit)

    return SpendConversionResponse(
        fuel_type=request.fuel_type,
        spend_amount=request.spend_amount,
        currency=request.currency,
        fuel_price=float(price.price_per_unit),
        price_unit=f"{price.currency}/{price.unit}",
        price_source=price.source,
        calculated_quantity=round(calculated_quantity, 2),
        quantity_unit=price.unit,
        formula=f"{request.spend_amount} {request.currency} ÷ {price.price_per_unit} {price.currency}/{price.unit} = {round(calculated_quantity, 2)} {price.unit}",
    )
