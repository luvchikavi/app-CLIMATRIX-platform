"""
Calculation Result - Output of the calculation pipeline.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List
from uuid import UUID


@dataclass
class CalculationResult:
    """
    Complete result from the calculation pipeline.

    Contains:
    - Emission values (CO2e, CO2, CH4, N2O)
    - WTT emissions for Scope 3.3
    - Factor metadata (what was used, source)
    - Calculation transparency (formula, confidence, warnings)
    """
    # Core emissions
    co2e_kg: Decimal
    co2_kg: Optional[Decimal] = None
    ch4_kg: Optional[Decimal] = None
    n2o_kg: Optional[Decimal] = None

    # WTT for automatic 3.3 tracking
    wtt_co2e_kg: Optional[Decimal] = None

    # Factor used
    emission_factor_id: Optional[UUID] = None
    factor_display_name: str = ""
    factor_source: str = ""
    factor_value: Decimal = Decimal("0")
    factor_unit: str = ""

    # Normalization info
    original_quantity: Decimal = Decimal("0")
    original_unit: str = ""
    converted_quantity: Decimal = Decimal("0")
    converted_unit: str = ""
    unit_conversion_applied: bool = False

    # Resolution info
    resolution_strategy: str = "exact"  # exact, region, global
    confidence: str = "high"  # high, medium, low

    # Transparency
    formula: str = ""
    warnings: List[str] = field(default_factory=list)

    # Metadata (Phase 9 - Source Documentation)
    factor_year: Optional[int] = None
    factor_region: str = ""
    method_hierarchy: Optional[str] = None  # "supplier", "ecoinvent", "defra_physical", "eeio_spend"
    fallback_used: bool = False
    fallback_reason: str = ""

    # T&D fields (Phase 3 - for future Carbon Footprint doc data)
    td_co2e_kg: Optional[Decimal] = None
    td_wtt_co2e_kg: Optional[Decimal] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "co2e_kg": float(self.co2e_kg),
            "co2_kg": float(self.co2_kg) if self.co2_kg else None,
            "ch4_kg": float(self.ch4_kg) if self.ch4_kg else None,
            "n2o_kg": float(self.n2o_kg) if self.n2o_kg else None,
            "wtt_co2e_kg": float(self.wtt_co2e_kg) if self.wtt_co2e_kg else None,
            "factor_used": self.factor_display_name,
            "factor_source": self.factor_source,
            "factor_value": float(self.factor_value) if self.factor_value else None,
            "factor_unit": self.factor_unit,
            "formula": self.formula,
            "confidence": self.confidence,
            "resolution_strategy": self.resolution_strategy,
            "warnings": self.warnings,
            "factor_year": self.factor_year,
            "factor_region": self.factor_region,
            "method_hierarchy": self.method_hierarchy,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "td_co2e_kg": float(self.td_co2e_kg) if self.td_co2e_kg else None,
            "td_wtt_co2e_kg": float(self.td_wtt_co2e_kg) if self.td_wtt_co2e_kg else None,
        }
