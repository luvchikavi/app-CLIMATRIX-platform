"""
WTT (Well-to-Tank) Service - Auto-calculates Scope 3.3 emissions.

WTT emissions represent the upstream emissions from:
- Extraction, refining, and transport of fuels (Scope 1)
- Generation, transmission, and distribution losses (Scope 2)

This service automatically maps Scope 1/2 activities to their WTT factors
and calculates the corresponding Scope 3.3 emissions.
"""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select

from app.models.emission import EmissionFactor, Emission, Activity


# Mapping of activity patterns to WTT factor activity_keys
# Pattern: (activity_key_pattern, target_unit) -> wtt_activity_key
WTT_MAPPING = {
    # Natural Gas (Scope 1.1)
    ("natural_gas_volume", "m3"): "wtt_natural_gas_m3",
    ("natural_gas_kwh", "kWh"): "wtt_natural_gas_kwh",
    ("natural_gas_kg", "kg"): "wtt_natural_gas_kg",

    # Diesel (Scope 1.1, 1.2)
    ("diesel_liters", "liters"): "wtt_diesel_liters",
    ("diesel_liters_mobile", "liters"): "wtt_diesel_liters",
    ("diesel_volume", "liters"): "wtt_diesel_liters",
    ("diesel_kg", "kg"): "wtt_diesel_kg",

    # Petrol/Gasoline (Scope 1.2)
    ("petrol_liters", "liters"): "wtt_petrol_liters",
    ("petrol_volume", "liters"): "wtt_petrol_liters",
    ("gasoline_liters", "liters"): "wtt_petrol_liters",
    ("gasoline_volume", "liters"): "wtt_petrol_liters",

    # LPG (Scope 1.1)
    ("lpg_liters", "liters"): "wtt_lpg_liters",
    ("lpg_volume", "liters"): "wtt_lpg_liters",
    ("lpg_kg", "kg"): "wtt_lpg_kg",

    # LNG (Scope 1.1)
    ("lng_liters", "liters"): "wtt_lng_liters",
    ("lng_volume", "liters"): "wtt_lng_liters",

    # Coal (Scope 1.1)
    ("coal_kg", "kg"): "wtt_coal_kg",
    ("coal_mass", "kg"): "wtt_coal_kg",

    # Fuel Oil (Scope 1.1)
    ("fuel_oil_liters", "liters"): "wtt_fuel_oil_liters",
    ("fuel_oil_volume", "liters"): "wtt_fuel_oil_liters",

    # Electricity (all regions use same WTT factor - T&D losses)
    ("electricity_uk", "kWh"): "wtt_electricity_kwh",
    ("electricity_us", "kWh"): "wtt_electricity_kwh",
    ("electricity_eu", "kWh"): "wtt_electricity_kwh",
    ("electricity_il", "kWh"): "wtt_electricity_kwh",
    ("electricity_global", "kWh"): "wtt_electricity_kwh",
    ("electricity", "kWh"): "wtt_electricity_kwh",

    # District heat/steam (Scope 2.2)
    ("district_heat_kwh", "kWh"): "wtt_heat_kwh",
    ("district_heat", "kWh"): "wtt_heat_kwh",
    ("steam_kwh", "kWh"): "wtt_steam_kwh",
    ("steam", "kWh"): "wtt_steam_kwh",

    # Vehicle fuels - Mobile (Scope 1.2)
    ("car_petrol_km", "km"): "wtt_car_petrol_km",
    ("car_diesel_km", "km"): "wtt_car_diesel_km",
    ("van_diesel_km", "km"): "wtt_van_diesel_km",
    ("hgv_diesel_km", "km"): "wtt_hgv_diesel_km",

    # Aviation fuel (Scope 3.6)
    ("flight_short_economy", "km"): "wtt_aviation_km",
    ("flight_long_economy", "km"): "wtt_aviation_km",
    ("flight_domestic", "km"): "wtt_aviation_km",
    ("flight_international", "km"): "wtt_aviation_km",

    # Rail fuel (Scope 3.6, 3.7)
    ("rail_national", "km"): "wtt_rail_km",
    ("rail_international", "km"): "wtt_rail_km",
}


class WTTService:
    """
    Service for WTT (Well-to-Tank) emissions calculation.

    WTT emissions are automatically calculated for Scope 1 and 2 activities
    and aggregated into Scope 3.3 (Fuel and Energy Related Activities).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def get_wtt_activity_key(self, activity_key: str, unit: str) -> Optional[str]:
        """Get the WTT factor activity_key for a given activity."""
        return WTT_MAPPING.get((activity_key, unit))

    async def get_wtt_factor(self, activity_key: str, unit: str) -> Optional[EmissionFactor]:
        """
        Get the WTT emission factor for an activity.

        Returns None if no WTT factor exists for this activity type.
        """
        wtt_key = self.get_wtt_activity_key(activity_key, unit)
        if not wtt_key:
            return None

        query = (
            select(EmissionFactor)
            .where(
                EmissionFactor.activity_key == wtt_key,
                EmissionFactor.is_active == True,
            )
            .order_by(EmissionFactor.year.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def calculate_wtt(
        self,
        activity_key: str,
        quantity: Decimal,
        unit: str
    ) -> Optional[Decimal]:
        """
        Calculate WTT emissions for an activity.

        Returns the WTT CO2e emissions in kg, or None if no WTT factor exists.
        """
        wtt_factor = await self.get_wtt_factor(activity_key, unit)
        if not wtt_factor:
            return None

        return quantity * wtt_factor.co2e_factor

    async def aggregate_wtt_for_period(self, period_id: UUID) -> dict:
        """
        Aggregate all WTT emissions for a reporting period.

        This sums up the wtt_co2e_kg from all Scope 1 and 2 emissions
        in the period. This total represents Scope 3.3 emissions.

        Returns:
            dict with:
            - total_wtt_co2e_kg: Total WTT emissions
            - by_source: Breakdown by Scope 1 vs Scope 2
            - activity_count: Number of activities with WTT
        """
        # Get all emissions for this period that have WTT
        query = (
            select(
                Activity.scope,
                func.sum(Emission.wtt_co2e_kg).label("wtt_total"),
                func.count(Emission.id).label("count")
            )
            .join(Emission, Emission.activity_id == Activity.id)
            .where(
                Activity.reporting_period_id == period_id,
                Emission.wtt_co2e_kg != None,
                Emission.wtt_co2e_kg > 0,
            )
            .group_by(Activity.scope)
        )

        result = await self.session.execute(query)
        rows = result.all()

        total_wtt = Decimal("0")
        by_source = {}
        activity_count = 0

        for row in rows:
            scope = row.scope
            wtt = row.wtt_total or Decimal("0")
            count = row.count or 0

            total_wtt += wtt
            activity_count += count

            source_name = f"Scope {scope} WTT"
            by_source[source_name] = {
                "co2e_kg": float(wtt),
                "activity_count": count,
            }

        return {
            "total_wtt_co2e_kg": float(total_wtt),
            "total_wtt_co2e_tonnes": float(total_wtt / 1000),
            "by_source": by_source,
            "activity_count": activity_count,
        }
