"""
Leased Assets Calculator - Categories 3.8, 3.13, 3.14.

Handles:
- 3.8: Upstream Leased Assets
- 3.13: Downstream Leased Assets
- 3.14: Franchises

Methods:
1. Tenant Emissions Pass-Through: Direct Scope 1+2 data from tenant/lessee
2. Area-Based: Emissions per m² using regional electricity intensity
3. Spend-Based: Monetary spend × EEIO factor (fallback)

Per GHG Protocol, tenant emissions pass-through is the most accurate method
when data is available.
"""
from decimal import Decimal
from typing import Optional

from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


class LeasedAssetsCalculator(BaseCalculator):
    """
    Calculator for leased assets, downstream leased, and franchises.

    Applicable categories:
    - 3.8: Upstream Leased Assets
    - 3.13: Downstream Leased Assets
    - 3.14: Franchises

    Methods:
    - tenant_passthrough: Direct Scope 1+2 from tenant (highest accuracy)
    - area_based: m² × regional intensity factor
    - spend_based: monetary value × EEIO factor (handled by SpendCalculator)
    """

    name = "leased_assets"
    applicable_categories = ["3.8", "3.13", "3.14"]

    # Default building energy intensity factors (kg CO2e per m² per year)
    # Source: CRREM, DEFRA 2024
    BUILDING_INTENSITY = {
        "office": Decimal("50.0"),       # Office building
        "retail": Decimal("65.0"),       # Retail/commercial
        "warehouse": Decimal("35.0"),    # Warehouse/logistics
        "industrial": Decimal("80.0"),   # Industrial/manufacturing
        "residential": Decimal("30.0"),  # Residential
        "hotel": Decimal("90.0"),        # Hotel/hospitality
        "healthcare": Decimal("120.0"),  # Healthcare facilities
        "education": Decimal("55.0"),    # Educational buildings
        "default": Decimal("50.0"),      # Default (office)
    }

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: Optional[EmissionFactor] = None,
    ) -> CalculationResult:
        """
        Calculate leased asset emissions.

        For tenant pass-through: quantity is direct CO2e in kg
        For area-based: quantity is m², factor is intensity per m²
        For spend-based: handled by parent SpendCalculator
        """
        result = self._base_calculation(normalized, factor, wtt_factor)

        # Add context about the method used
        activity_key = factor.activity_key if factor else ""

        if "tenant" in activity_key or "passthrough" in activity_key:
            result.confidence = "high"
            result.warnings.append(
                "Using tenant-reported Scope 1+2 emissions (most accurate method)."
            )
        elif "area" in activity_key or factor.activity_unit == "m2":
            result.confidence = "medium"
            result.warnings.append(
                "Using area-based estimation with regional building intensity factor. "
                "Consider requesting tenant-specific data for higher accuracy."
            )
        else:
            result.confidence = "low"
            result.warnings.append(
                "Using spend-based estimation. This has the lowest accuracy. "
                "Consider requesting tenant emission data or using area-based method."
            )

        return result

    @classmethod
    def calculate_tenant_passthrough(
        cls,
        tenant_scope1_co2e_kg: Decimal,
        tenant_scope2_co2e_kg: Decimal,
        source_documentation: str = "",
    ) -> CalculationResult:
        """
        Calculate using tenant-reported Scope 1 and 2 emissions.

        This is the most accurate method per GHG Protocol.
        The tenant provides their actual Scope 1 and Scope 2 totals.

        Args:
            tenant_scope1_co2e_kg: Tenant's Scope 1 emissions in kg CO2e
            tenant_scope2_co2e_kg: Tenant's Scope 2 emissions in kg CO2e
            source_documentation: Source/reference for the data

        Returns:
            CalculationResult with combined emissions
        """
        total_co2e = tenant_scope1_co2e_kg + tenant_scope2_co2e_kg

        formula = (
            f"Tenant Scope 1: {tenant_scope1_co2e_kg:.2f} kg + "
            f"Tenant Scope 2: {tenant_scope2_co2e_kg:.2f} kg = "
            f"{total_co2e:.2f} kg CO2e"
        )

        warnings = [
            "Using tenant-reported Scope 1+2 emissions (pass-through method). "
            "This is the most accurate approach per GHG Protocol."
        ]
        if source_documentation:
            warnings.append(f"Source: {source_documentation}")

        return CalculationResult(
            co2e_kg=total_co2e,
            co2_kg=None,
            ch4_kg=None,
            n2o_kg=None,
            wtt_co2e_kg=None,
            emission_factor_id=None,
            factor_display_name="Tenant Emissions Pass-Through",
            factor_source="Tenant-Reported",
            factor_value=Decimal("1.0"),
            factor_unit="kg CO2e (direct)",
            original_quantity=total_co2e,
            original_unit="kg CO2e",
            converted_quantity=total_co2e,
            converted_unit="kg CO2e",
            unit_conversion_applied=False,
            resolution_strategy="tenant_passthrough",
            confidence="high",
            formula=formula,
            warnings=warnings,
        )

    @classmethod
    def calculate_area_based(
        cls,
        area_m2: Decimal,
        building_type: str = "default",
        country_code: str = "Global",
        custom_intensity: Optional[Decimal] = None,
    ) -> CalculationResult:
        """
        Calculate using area-based method.

        Formula: emissions = area_m² × intensity_factor (kg CO2e/m²/year)

        Args:
            area_m2: Floor area in square meters
            building_type: Type of building (office, retail, warehouse, etc.)
            country_code: Country for regional adjustment
            custom_intensity: Override default intensity factor

        Returns:
            CalculationResult with area-based emissions
        """
        # Get intensity factor
        if custom_intensity is not None:
            intensity = custom_intensity
        else:
            intensity = cls.BUILDING_INTENSITY.get(
                building_type.lower(),
                cls.BUILDING_INTENSITY["default"]
            )

        total_co2e = area_m2 * intensity

        formula = (
            f"{area_m2} m² × {intensity} kg CO2e/m²/year = "
            f"{total_co2e:.2f} kg CO2e"
        )

        return CalculationResult(
            co2e_kg=total_co2e,
            co2_kg=None,
            ch4_kg=None,
            n2o_kg=None,
            wtt_co2e_kg=None,
            emission_factor_id=None,
            factor_display_name=f"Building Intensity ({building_type})",
            factor_source="CRREM/DEFRA 2024",
            factor_value=intensity,
            factor_unit="kg CO2e/m²/year",
            original_quantity=area_m2,
            original_unit="m2",
            converted_quantity=area_m2,
            converted_unit="m2",
            unit_conversion_applied=False,
            resolution_strategy="area_based",
            confidence="medium",
            formula=formula,
            warnings=[
                f"Area-based estimate using {building_type} building intensity of "
                f"{intensity} kg CO2e/m²/year. Consider using tenant-specific data."
            ],
        )
