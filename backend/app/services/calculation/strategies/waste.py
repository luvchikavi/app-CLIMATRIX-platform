"""
Waste Calculator - Scope 3.5 and 3.12

Handles waste-related emissions:
- Scope 3.5: Waste Generated in Operations
- Scope 3.12: End-of-Life Treatment of Sold Products

Disposal methods:
- Landfill (with/without gas capture)
- Incineration (with/without energy recovery)
- Recycling
- Composting
- Anaerobic digestion

GHG Protocol: Scope 3, Categories 5 and 12
"""
from decimal import Decimal
from typing import Optional

from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


class WasteCalculator(BaseCalculator):
    """
    Calculator for waste emissions (Scope 3.5, 3.12).

    Formula: CO2e = mass_kg × disposal_factor

    Disposal factors vary significantly by:
    - Waste type (organic, plastic, paper, metal, etc.)
    - Disposal method (landfill, incineration, recycling)
    - Region (landfill gas capture rates vary)

    Note: Recycling typically has negative or near-zero factors
    due to avoided virgin material production.
    """

    name = "waste"
    applicable_categories = ["3.5", "3.12"]

    # Common waste types and their typical disposal routes
    WASTE_TYPES = {
        "mixed_waste": "General mixed waste",
        "organic_waste": "Food and garden waste",
        "paper_cardboard": "Paper and cardboard",
        "plastic_mixed": "Mixed plastics",
        "metal_mixed": "Mixed metals",
        "glass": "Glass",
        "construction": "Construction and demolition",
        "electronic": "WEEE/E-waste",
        "hazardous": "Hazardous waste",
    }

    # Disposal methods
    DISPOSAL_METHODS = {
        "landfill": "Landfill disposal",
        "landfill_gas_capture": "Landfill with gas capture",
        "incineration": "Incineration without energy recovery",
        "incineration_energy": "Incineration with energy recovery",
        "recycling": "Recycling",
        "composting": "Composting",
        "anaerobic_digestion": "Anaerobic digestion",
    }

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: Optional[EmissionFactor] = None,
    ) -> CalculationResult:
        """
        Calculate waste emissions.

        Args:
            normalized: Mass in kg (normalized)
            factor: Emission factor (kg CO2e/kg waste)
            wtt_factor: Not typically used for waste

        Returns:
            CalculationResult with emissions breakdown
        """
        mass_kg = normalized.quantity

        # Calculate CO2e
        co2e_kg = mass_kg * factor.co2e_factor

        # Build formula
        formula = (
            f"{normalized.original_quantity} {normalized.original_unit}"
        )
        if normalized.conversion_applied:
            formula += f" → {mass_kg:.2f} kg"
        formula += f" × {factor.co2e_factor} kg CO2e/kg = {co2e_kg:.2f} kg CO2e"

        # Determine confidence based on disposal specificity
        confidence = "high"
        warnings = []

        # Check if using generic factors
        if "mixed" in (factor.activity_key or "").lower():
            confidence = "medium"
            warnings.append(
                "Using mixed waste factor - more specific waste type would improve accuracy"
            )

        # Recycling can have negative emissions (avoided production)
        if co2e_kg < 0:
            warnings.append(
                "Negative emissions represent avoided virgin material production"
            )

        return CalculationResult(
            co2e_kg=co2e_kg,
            co2_kg=None,
            ch4_kg=None,  # Landfill CH4 is in CO2e factor
            n2o_kg=None,
            wtt_co2e_kg=None,  # No WTT for waste typically
            emission_factor_id=factor.id,
            factor_display_name=factor.display_name,
            factor_source=factor.source,
            factor_value=factor.co2e_factor,
            factor_unit=factor.factor_unit,
            original_quantity=normalized.original_quantity,
            original_unit=normalized.original_unit,
            converted_quantity=mass_kg,
            converted_unit="kg",
            unit_conversion_applied=normalized.conversion_applied,
            formula=formula,
            confidence=confidence,
            warnings=warnings,
        )

    @staticmethod
    def get_activity_key(waste_type: str, disposal_method: str) -> str:
        """
        Build activity_key from waste type and disposal method.

        Example: waste_paper_recycling, waste_organic_composting
        """
        return f"waste_{waste_type}_{disposal_method}"
