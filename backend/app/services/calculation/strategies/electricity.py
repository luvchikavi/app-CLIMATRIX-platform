"""
Electricity Calculator - Scope 2 (Purchased Energy).

Handles: Grid electricity, district heating, steam, cooling.
Supports: Location-based and market-based methods.
Formula: quantity × grid_factor (location) or supplier_factor (market)

Also calculates Scope 3.3 components:
- T&D losses: emissions from electricity lost in transmission & distribution
- WTT of T&D: upstream emissions for electricity lost in T&D
"""
from decimal import Decimal

from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


class ElectricityCalculator(BaseCalculator):
    """
    Calculator for purchased energy (Scope 2).

    Applicable categories:
    - 2: Purchased electricity, heat, steam, cooling

    Methods:
    - Location-based: Uses grid average emission factor for region
    - Market-based: Uses supplier-specific factor (if available)

    Special behavior:
    - Calculates T&D losses and WTT for Scope 3.3
    - Region-specific factors (IL, UK, US, EU have different grid mixes)
    """

    applicable_categories = ["2", "2.1", "2.2"]

    @property
    def name(self) -> str:
        return "electricity"

    def _get_country_code(self, factor: EmissionFactor) -> str:
        """Extract country code from emission factor."""
        if factor.region and factor.region != "Global":
            return factor.region.upper()
        # Try to extract from activity_key
        key = factor.activity_key.lower()
        country_map = {
            "il": "IL", "uk": "UK", "gb": "UK", "us": "US",
            "de": "DE", "fr": "FR", "es": "ES", "it": "IT",
            "nl": "NL", "pl": "PL", "eu": "EU", "au": "AU",
            "ca": "CA", "cn": "CN", "in": "IN", "jp": "JP",
            "kr": "KR", "br": "BR",
        }
        for code, country in country_map.items():
            if f"_{code}" in key or key.endswith(f"_{code}"):
                return country
        return "Global"

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: EmissionFactor | None = None,
    ) -> CalculationResult:
        """
        Calculate Scope 2 emissions from purchased energy.
        Also calculates T&D and WTT components for Scope 3.3.
        """
        result = self._base_calculation(normalized, factor, wtt_factor)

        # Electricity-specific context
        if "il" in factor.activity_key.lower() or factor.region == "IL":
            result.warnings.append(
                "Using Noga voluntary mechanism grid factor (Israel)"
            )
        elif "uk" in factor.activity_key.lower() or factor.region == "UK":
            result.warnings.append(
                "Using UK National Grid factor"
            )
        elif factor.region == "Global":
            result.warnings.append(
                "Using global average grid factor. Consider using region-specific factor for accuracy."
            )

        # WTT for electricity (T&D losses + upstream)
        if wtt_factor:
            result.warnings.append(
                f"T&D and generation losses of {result.wtt_co2e_kg:.2f} kg CO2e will be added to Scope 3.3"
            )

        # Calculate T&D and T&D WTT from per-country factors
        try:
            from app.data.reference_data import get_wtt_td_factors
            country_code = self._get_country_code(factor)
            td_factors = get_wtt_td_factors(country_code)

            if td_factors and normalized.quantity:
                kwh = normalized.quantity
                td_loss = kwh * td_factors["td_loss"]
                td_wtt = kwh * td_factors["td_wtt"]
                result.td_co2e_kg = td_loss
                result.td_wtt_co2e_kg = td_wtt
                result.factor_region = country_code
                result.warnings.append(
                    f"Scope 3.3: T&D losses = {float(td_loss):.2f} kg CO2e, "
                    f"T&D WTT = {float(td_wtt):.2f} kg CO2e "
                    f"(source: {td_factors['source']})"
                )
        except ImportError:
            pass

        return result
