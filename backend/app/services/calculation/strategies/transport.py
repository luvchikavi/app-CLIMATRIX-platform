"""
Transport/Freight Calculator - Scope 3.4 and 3.9

Handles upstream and downstream transportation emissions:
- Scope 3.4: Upstream Transportation and Distribution
- Scope 3.9: Downstream Transportation and Distribution

Supports multiple transport modes:
- Road freight (HGV, van, etc.)
- Rail freight
- Sea freight
- Air freight

GHG Protocol: Scope 3, Categories 4 and 9
"""
from decimal import Decimal
from typing import Optional

from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


class TransportCalculator(BaseCalculator):
    """
    Calculator for freight/transport emissions (Scope 3.4, 3.9).

    Formula depends on data availability:
    1. Tonne-km method: CO2e = weight_tonnes × distance_km × factor
    2. Distance-only method: CO2e = distance_km × factor (assumes average load)
    3. Spend method: CO2e = spend × EEIO_factor

    Transport modes supported:
    - road_freight_hgv: Heavy Goods Vehicle
    - road_freight_van: Van delivery
    - rail_freight: Rail transport
    - sea_freight_container: Container shipping
    - sea_freight_bulk: Bulk shipping
    - air_freight: Air cargo
    """

    name = "transport"
    applicable_categories = ["3.4", "3.9"]

    # Default load factors (tonnes) for distance-only calculations
    DEFAULT_LOADS = {
        "road_freight_hgv": Decimal("10.0"),  # Average HGV load
        "road_freight_van": Decimal("0.5"),   # Average van load
        "rail_freight": Decimal("500.0"),     # Per wagon
        "sea_freight_container": Decimal("14.0"),  # TEU average
        "air_freight": Decimal("5.0"),        # Average cargo
    }

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: Optional[EmissionFactor] = None,
        weight_tonnes: Optional[Decimal] = None,
    ) -> CalculationResult:
        """
        Calculate transport emissions.

        Args:
            normalized: Distance in km or tonne-km (normalized)
            factor: Emission factor (kg CO2e/tonne-km or kg CO2e/km)
            wtt_factor: Well-to-tank factor for fuel
            weight_tonnes: Optional weight for tonne-km calculation

        Returns:
            CalculationResult with emissions breakdown
        """
        quantity = normalized.quantity
        unit = normalized.unit

        # Determine calculation method
        if "tonne" in unit.lower() or "tkm" in unit.lower():
            # Already in tonne-km
            tonne_km = quantity
            method = "tonne-km"
        elif weight_tonnes:
            # Distance × weight
            tonne_km = quantity * weight_tonnes
            method = "distance × weight"
        else:
            # Distance only - use default load assumption
            default_load = self.DEFAULT_LOADS.get(
                factor.activity_key,
                Decimal("1.0")
            )
            tonne_km = quantity * default_load
            method = f"distance × {default_load}t (assumed)"

        # Calculate CO2e
        co2e_kg = tonne_km * factor.co2e_factor

        # WTT emissions
        wtt_co2e_kg = None
        if wtt_factor:
            wtt_co2e_kg = tonne_km * wtt_factor.co2e_factor

        # Build formula
        formula_parts = [f"{normalized.original_quantity} {normalized.original_unit}"]
        if normalized.conversion_applied:
            formula_parts.append(f"→ {quantity:.2f} {unit}")
        if weight_tonnes:
            formula_parts.append(f"× {weight_tonnes} tonnes")
        formula_parts.append(f"× {factor.co2e_factor} kg CO2e/tonne-km")
        formula_parts.append(f"= {co2e_kg:.2f} kg CO2e")

        warnings = []
        if method.startswith("distance × ") and "assumed" in method:
            warnings.append(f"Weight not provided - using average load assumption ({method})")

        return CalculationResult(
            co2e_kg=co2e_kg,
            co2_kg=None,
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
            converted_quantity=tonne_km,
            converted_unit="tonne-km",
            unit_conversion_applied=normalized.conversion_applied,
            formula=" ".join(formula_parts),
            confidence="high" if weight_tonnes else "medium",
            warnings=warnings,
        )


class FreightCalculator(TransportCalculator):
    """Alias for TransportCalculator - same logic applies."""
    name = "freight"
