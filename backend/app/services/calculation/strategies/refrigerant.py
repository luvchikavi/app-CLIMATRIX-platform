"""
Refrigerant Calculator - Scope 1.3 Fugitive Emissions

Handles refrigerant and other fugitive gas emissions:
- Air conditioning systems
- Refrigeration equipment
- Fire suppression systems
- Electrical equipment (SF6)

Uses Global Warming Potential (GWP) values to convert to CO2e.

GHG Protocol: Scope 1, Category 1.3 - Fugitive Emissions
"""
from decimal import Decimal
from typing import Optional

from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


# GWP fallback values - MUST match the database emission_factors.py values.
# The database is the primary source; these are ONLY used if DB lookup fails.
# Source: DEFRA 2024 v1.1 - Refrigerant & other (AR5 GWP basis).
# All values verified against DEFRA 2024 flat file spreadsheet.
GWP_FALLBACK = {
    # HFCs - Kyoto Protocol (DEFRA 2024, AR5 GWP)
    "R-134a": Decimal("1300"),     # DEFRA 2024: Kyoto > HFC-134a
    "R-32": Decimal("677"),        # DEFRA 2024: Kyoto > HFC-32
    "R-125": Decimal("3170"),      # DEFRA 2024: Kyoto > HFC-125
    "R-143a": Decimal("4800"),     # DEFRA 2024: Kyoto > HFC-143a
    "R-227ea": Decimal("3350"),    # DEFRA 2024: Kyoto > HFC-227ea
    "HFC-23": Decimal("12400"),    # DEFRA 2024: Kyoto > HFC-23
    "HFC-152a": Decimal("138"),    # DEFRA 2024: Kyoto > HFC-152a

    # Blends (DEFRA 2024, AR5 GWP)
    "R-410A": Decimal("1924"),     # DEFRA 2024: Blends > R410A
    "R-407C": Decimal("1624"),     # DEFRA 2024: Blends > R407C
    "R-404A": Decimal("3943"),     # DEFRA 2024: Blends > R404A
    "R-507A": Decimal("3985"),     # DEFRA 2024: Blends > R507A

    # HCFCs - Montreal Protocol (DEFRA 2024, AR5 GWP)
    "R-22": Decimal("1760"),       # DEFRA 2024: Montreal > HCFC-22
    "R-123": Decimal("79"),        # DEFRA 2024: Montreal > HCFC-123

    # Natural refrigerants (DEFRA 2024: Other products)
    "R-290": Decimal("0.06"),      # DEFRA 2024: Other > propane
    "R-600a": Decimal("3"),        # DEFRA 2024: Other > isobutane
    "R-717": Decimal("0"),         # Ammonia (not in DEFRA, negligible GWP)
    "R-744": Decimal("1"),         # CO2

    # Other gases (DEFRA 2024: Kyoto)
    "SF6": Decimal("23500"),       # DEFRA 2024: Kyoto > SF6
    "NF3": Decimal("16100"),       # DEFRA 2024: Kyoto > Nitrogen trifluoride
    "PFCs": Decimal("9200"),       # DEFRA 2024: Kyoto > Perfluorocyclopropane (representative)

    # Fire suppression (DEFRA 2024: Montreal + Other)
    "Halon-1211": Decimal("1750"), # DEFRA 2024: Montreal > Halon-1211
    "FK-5-1-12": Decimal("1"),     # Novec 1230 (negligible GWP)
    "R-1234yf": Decimal("1"),      # DEFRA 2024: Other > R1234yf
}


class RefrigerantCalculator(BaseCalculator):
    """
    Calculator for refrigerant/fugitive emissions (Scope 1.3).

    Formula: CO2e = leaked_mass_kg × GWP

    This is conceptually simple (direct multiplication by GWP)
    but requires accurate tracking of:
    - Refrigerant type (for correct GWP)
    - Leaked quantity (not total charge)

    Typical sources:
    - Equipment leakage during operation
    - Refills/top-ups (indicates previous leakage)
    - End-of-life disposal (if not recovered)
    """

    name = "refrigerant"
    applicable_categories = ["1.3"]

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: Optional[EmissionFactor] = None,
    ) -> CalculationResult:
        """
        Calculate refrigerant emissions.

        Args:
            normalized: Leaked mass in kg (normalized)
            factor: GWP factor (kg CO2e/kg refrigerant = GWP value)
            wtt_factor: Not used for refrigerants

        Returns:
            CalculationResult with emissions breakdown
        """
        mass_kg = normalized.quantity

        # The factor for refrigerants IS the GWP value
        gwp = factor.co2e_factor

        # Calculate CO2e
        co2e_kg = mass_kg * gwp

        # Build formula
        formula = (
            f"{normalized.original_quantity} {normalized.original_unit}"
        )
        if normalized.conversion_applied:
            formula += f" → {mass_kg:.4f} kg"
        formula += f" × {gwp} GWP = {co2e_kg:.2f} kg CO2e"

        # Confidence is high if we have exact refrigerant type
        confidence = "high"
        warnings = []

        # Check for very high emissions (sanity check)
        if co2e_kg > 100000:  # 100 tonnes CO2e
            warnings.append(
                f"High emission value ({co2e_kg/1000:.1f} tonnes CO2e) - "
                "please verify leaked quantity is correct"
            )

        return CalculationResult(
            co2e_kg=co2e_kg,
            co2_kg=None,  # Refrigerants are 100% synthetic GHGs
            ch4_kg=None,
            n2o_kg=None,
            wtt_co2e_kg=None,  # No WTT for refrigerants
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
    def get_gwp(refrigerant_type: str) -> Optional[Decimal]:
        """
        Get GWP value for a refrigerant type.

        Args:
            refrigerant_type: e.g., "R-134a", "R-410A", "SF6"

        Returns:
            GWP value or None if not found
        """
        # Normalize input
        normalized = refrigerant_type.upper().replace(" ", "").replace("_", "-")

        # Try exact match
        if normalized in GWP_FALLBACK:
            return GWP_FALLBACK[normalized]

        # Try with R- prefix
        if not normalized.startswith("R-"):
            with_prefix = f"R-{normalized}"
            if with_prefix in GWP_FALLBACK:
                return GWP_FALLBACK[with_prefix]

        return None

    @staticmethod
    def estimate_annual_leakage(
        charge_kg: Decimal,
        equipment_type: str = "commercial_refrigeration"
    ) -> Decimal:
        """
        Estimate annual refrigerant leakage based on equipment type.

        Default leakage rates (IPCC guidelines):
        - Domestic refrigeration: 0.5-3%
        - Commercial refrigeration: 10-35%
        - Industrial refrigeration: 7-25%
        - Transport refrigeration: 15-50%
        - Air conditioning (commercial): 2-15%
        - Air conditioning (residential): 1-10%
        - Chillers: 2-15%
        """
        LEAKAGE_RATES = {
            "domestic_refrigeration": Decimal("0.02"),
            "commercial_refrigeration": Decimal("0.15"),
            "industrial_refrigeration": Decimal("0.10"),
            "transport_refrigeration": Decimal("0.25"),
            "commercial_ac": Decimal("0.08"),
            "residential_ac": Decimal("0.05"),
            "chiller": Decimal("0.05"),
        }

        rate = LEAKAGE_RATES.get(equipment_type, Decimal("0.10"))
        return charge_kg * rate
