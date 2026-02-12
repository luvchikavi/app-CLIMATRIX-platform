"""
Flight Calculator - Scope 3.6 Business Travel (Air)

Handles flight emissions with:
- Radiative Forcing (RF) multiplier for high-altitude effects
- Class-based factors (economy, business, first)
- Distance-based factors (short-haul, medium-haul, long-haul)

GHG Protocol: Scope 3, Category 6 - Business Travel
"""
from decimal import Decimal
from typing import Optional

from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


# Radiative Forcing multiplier (accounts for non-CO2 climate effects at altitude)
# DEFRA recommends 1.9, but this is configurable
RF_MULTIPLIER = Decimal("1.9")

# Distance thresholds (km)
SHORT_HAUL_MAX = 1500
MEDIUM_HAUL_MAX = 4000


class FlightCalculator(BaseCalculator):
    """
    Calculator for air travel emissions (Scope 3.6).

    Formula: CO2e = distance_km × factor × RF_multiplier × class_multiplier

    Notes:
    - RF multiplier accounts for contrails, NOx, and other high-altitude effects
    - Class multipliers: Economy=1.0, Business=2.9, First=4.0 (based on seat space)
    - Distance categories affect emission factors (takeoff/landing overhead)
    """

    name = "flight"
    applicable_categories = ["3.6"]

    # Class multipliers (relative to economy)
    CLASS_MULTIPLIERS = {
        "economy": Decimal("1.0"),
        "premium_economy": Decimal("1.6"),
        "business": Decimal("2.9"),
        "first": Decimal("4.0"),
    }

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: Optional[EmissionFactor] = None,
        travel_class: str = "economy",
        include_rf: bool = True,
    ) -> CalculationResult:
        """
        Calculate flight emissions.

        Args:
            normalized: Distance in km (normalized)
            factor: Base emission factor (kg CO2e/passenger-km)
            wtt_factor: Well-to-tank factor for jet fuel
            travel_class: economy, premium_economy, business, first
            include_rf: Whether to apply RF multiplier

        Returns:
            CalculationResult with emissions breakdown
        """
        distance_km = normalized.quantity

        # Get class multiplier
        class_mult = self.CLASS_MULTIPLIERS.get(
            travel_class.lower(),
            Decimal("1.0")
        )

        # Get RF multiplier (if enabled)
        rf_mult = RF_MULTIPLIER if include_rf else Decimal("1.0")

        # Base CO2e calculation
        base_co2e = distance_km * factor.co2e_factor

        # Apply multipliers
        co2e_kg = base_co2e * class_mult * rf_mult

        # WTT emissions (upstream jet fuel extraction/refining)
        wtt_co2e_kg = None
        if wtt_factor:
            wtt_co2e_kg = distance_km * wtt_factor.co2e_factor * class_mult

        # Build formula string
        formula_parts = [
            f"{normalized.original_quantity} {normalized.original_unit}"
        ]
        if normalized.conversion_applied:
            formula_parts.append(f"→ {distance_km:.2f} km")
        formula_parts.append(f"× {factor.co2e_factor} kg CO2e/km")
        if class_mult != Decimal("1.0"):
            formula_parts.append(f"× {class_mult} ({travel_class})")
        if include_rf:
            formula_parts.append(f"× {rf_mult} (RF)")
        formula_parts.append(f"= {co2e_kg:.2f} kg CO2e")

        return CalculationResult(
            co2e_kg=co2e_kg,
            co2_kg=None,  # Flights typically report total CO2e only
            ch4_kg=None,
            n2o_kg=None,
            wtt_co2e_kg=wtt_co2e_kg,
            emission_factor_id=factor.id,
            factor_display_name=factor.display_name,
            factor_source=factor.source,
            factor_value=factor.co2e_factor,
            factor_unit=factor.factor_unit,
            original_quantity=normalized.original_quantity,
            original_unit=normalized.original_unit,
            converted_quantity=distance_km,
            converted_unit="km",
            unit_conversion_applied=normalized.conversion_applied,
            formula=" ".join(formula_parts),
            confidence="high",
            warnings=[],
        )

    @staticmethod
    def get_distance_category(distance_km: Decimal) -> str:
        """Determine flight distance category."""
        if distance_km <= SHORT_HAUL_MAX:
            return "short_haul"
        elif distance_km <= MEDIUM_HAUL_MAX:
            return "medium_haul"
        else:
            return "long_haul"

    @staticmethod
    def estimate_distance(origin: str, destination: str) -> Optional[Decimal]:
        """
        Estimate great-circle distance between airports using Haversine formula.

        Args:
            origin: IATA code (e.g., "TLV")
            destination: IATA code (e.g., "LHR")

        Returns:
            Distance in km as Decimal, or None if airport not found.
        """
        from app.data.airports import calculate_flight_distance

        distance = calculate_flight_distance(origin.upper(), destination.upper())
        if distance is None:
            return None
        return Decimal(str(round(distance, 1)))
