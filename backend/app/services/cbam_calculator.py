"""
CBAM Calculation Engine.

Implements EU CBAM (Carbon Border Adjustment Mechanism) calculations:
- Embedded emissions (direct + indirect)
- Specific Embedded Emissions (SEE) per tonne of product
- Carbon price deduction for third-country carbon pricing
- CBAM certificate requirements (definitive phase from 2026)

Reference: EU Regulation 2023/956 and Implementing Regulation 2023/1773
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from datetime import date

from app.data.cbam_data import (
    get_default_see_by_cn_code,
    get_grid_factor_by_country,
    get_sector_for_cn_code,
)


class CBAMCalculator:
    """Calculator for CBAM embedded emissions and certificate requirements."""

    # Default values per EU regulation
    DEFAULT_ELECTRICITY_FACTOR = Decimal("0.5")  # tCO2e/MWh default if country unknown
    CERTIFICATE_TONNES = Decimal("1")  # 1 CBAM certificate = 1 tonne CO2e

    def __init__(self):
        """Initialize the CBAM calculator."""
        pass

    def calculate_embedded_emissions(
        self,
        cn_code: str,
        mass_tonnes: Decimal,
        country_code: str,
        actual_direct_see: Optional[Decimal] = None,
        actual_indirect_see: Optional[Decimal] = None,
        electricity_consumption_mwh: Optional[Decimal] = None,
        use_default_values: bool = True,
    ) -> dict:
        """
        Calculate embedded emissions for an imported product.

        Per CBAM regulation, embedded emissions include:
        - Direct emissions: From production process (furnaces, reactions, etc.)
        - Indirect emissions: From electricity consumed during production

        Args:
            cn_code: CN (Combined Nomenclature) code for the product
            mass_tonnes: Mass of imported product in tonnes
            country_code: ISO country code of production facility
            actual_direct_see: Actual direct SEE from installation (if available)
            actual_indirect_see: Actual indirect SEE from installation (if available)
            electricity_consumption_mwh: Actual electricity consumption (if available)
            use_default_values: Whether to use EU default values when actuals unavailable

        Returns:
            Dictionary with calculation results including total embedded emissions
        """
        result = {
            "cn_code": cn_code,
            "mass_tonnes": mass_tonnes,
            "country_code": country_code,
            "calculation_method": "actual" if actual_direct_see else "default",
            "direct_emissions_tco2e": Decimal("0"),
            "indirect_emissions_tco2e": Decimal("0"),
            "total_emissions_tco2e": Decimal("0"),
            "direct_see": Decimal("0"),
            "indirect_see": Decimal("0"),
            "total_see": Decimal("0"),
            "warnings": [],
        }

        # Get default values for this CN code
        defaults = get_default_see_by_cn_code(cn_code)

        # Determine direct SEE
        if actual_direct_see is not None:
            direct_see = actual_direct_see
            result["calculation_method"] = "actual"
        elif defaults and use_default_values:
            direct_see = defaults["direct_see"]
            result["calculation_method"] = "default"
            result["warnings"].append(f"Using EU default direct SEE: {direct_see} tCO2e/t")
        else:
            direct_see = Decimal("0")
            result["warnings"].append("No direct SEE available - using zero")

        # Determine indirect SEE
        if actual_indirect_see is not None:
            indirect_see = actual_indirect_see
        elif electricity_consumption_mwh is not None and mass_tonnes > 0:
            # Calculate from electricity consumption and grid factor
            grid_factor = get_grid_factor_by_country(country_code)
            if grid_factor == Decimal("0"):
                grid_factor = self.DEFAULT_ELECTRICITY_FACTOR
                result["warnings"].append(
                    f"Unknown grid factor for {country_code}, using default {grid_factor} tCO2e/MWh"
                )
            indirect_see = (electricity_consumption_mwh * grid_factor) / mass_tonnes
        elif defaults and use_default_values:
            indirect_see = defaults["indirect_see"]
            result["warnings"].append(f"Using EU default indirect SEE: {indirect_see} tCO2e/t")
        else:
            indirect_see = Decimal("0")
            result["warnings"].append("No indirect SEE available - using zero")

        # Calculate total SEE
        total_see = direct_see + indirect_see

        # Calculate total embedded emissions
        direct_emissions = (direct_see * mass_tonnes).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )
        indirect_emissions = (indirect_see * mass_tonnes).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )
        total_emissions = direct_emissions + indirect_emissions

        result.update({
            "direct_see": direct_see,
            "indirect_see": indirect_see,
            "total_see": total_see,
            "direct_emissions_tco2e": direct_emissions,
            "indirect_emissions_tco2e": indirect_emissions,
            "total_emissions_tco2e": total_emissions,
        })

        return result

    def calculate_carbon_price_deduction(
        self,
        total_emissions_tco2e: Decimal,
        foreign_carbon_price_eur: Optional[Decimal] = None,
        foreign_free_allocation_pct: Decimal = Decimal("0"),
        eu_ets_price_eur: Decimal = Decimal("80"),
        eu_free_allocation_pct: Decimal = Decimal("0"),
    ) -> dict:
        """
        Calculate carbon price deduction for third-country carbon pricing.

        CBAM allows deduction of carbon prices effectively paid in the country
        of origin, to avoid double charging.

        Args:
            total_emissions_tco2e: Total embedded emissions to be adjusted
            foreign_carbon_price_eur: Carbon price paid in country of origin (EUR/tCO2e)
            foreign_free_allocation_pct: Free allocation percentage in foreign country (0-100)
            eu_ets_price_eur: Current EU ETS price (EUR/tCO2e)
            eu_free_allocation_pct: EU free allocation percentage for this sector (0-100)

        Returns:
            Dictionary with deduction calculation and net CBAM liability
        """
        result = {
            "total_emissions_tco2e": total_emissions_tco2e,
            "foreign_carbon_price_eur": foreign_carbon_price_eur or Decimal("0"),
            "foreign_free_allocation_pct": foreign_free_allocation_pct,
            "eu_ets_price_eur": eu_ets_price_eur,
            "eu_free_allocation_pct": eu_free_allocation_pct,
            "deduction_tco2e": Decimal("0"),
            "net_emissions_tco2e": total_emissions_tco2e,
            "gross_cbam_cost_eur": Decimal("0"),
            "deduction_eur": Decimal("0"),
            "net_cbam_cost_eur": Decimal("0"),
        }

        if total_emissions_tco2e <= 0:
            return result

        # Calculate effective emissions after EU free allocation
        eu_covered_emissions = total_emissions_tco2e * (
            (Decimal("100") - eu_free_allocation_pct) / Decimal("100")
        )

        # Calculate gross CBAM cost (before deductions)
        gross_cbam_cost = (eu_covered_emissions * eu_ets_price_eur).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Calculate deduction for foreign carbon price
        deduction_eur = Decimal("0")
        deduction_tco2e = Decimal("0")

        if foreign_carbon_price_eur and foreign_carbon_price_eur > 0:
            # Effective foreign price after their free allocation
            effective_foreign_emissions = total_emissions_tco2e * (
                (Decimal("100") - foreign_free_allocation_pct) / Decimal("100")
            )

            # Deduction is the lower of: foreign price paid OR EU ETS price
            foreign_total_paid = effective_foreign_emissions * foreign_carbon_price_eur

            # Cap deduction at actual foreign payment
            deduction_eur = min(foreign_total_paid, gross_cbam_cost).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Convert deduction to equivalent tonnes
            if eu_ets_price_eur > 0:
                deduction_tco2e = (deduction_eur / eu_ets_price_eur).quantize(
                    Decimal("0.001"), rounding=ROUND_HALF_UP
                )

        # Net CBAM liability
        net_cbam_cost = max(Decimal("0"), gross_cbam_cost - deduction_eur)
        net_emissions = max(Decimal("0"), eu_covered_emissions - deduction_tco2e)

        result.update({
            "deduction_tco2e": deduction_tco2e,
            "net_emissions_tco2e": net_emissions,
            "gross_cbam_cost_eur": gross_cbam_cost,
            "deduction_eur": deduction_eur,
            "net_cbam_cost_eur": net_cbam_cost,
        })

        return result

    def calculate_certificate_requirement(
        self,
        net_emissions_tco2e: Decimal,
        eu_ets_price_eur: Decimal = Decimal("80"),
    ) -> dict:
        """
        Calculate CBAM certificate requirements for definitive phase (2026+).

        In the definitive phase, importers must surrender CBAM certificates
        corresponding to the embedded emissions, minus any deductions.

        Args:
            net_emissions_tco2e: Net embedded emissions after deductions
            eu_ets_price_eur: Current EU ETS price for certificate valuation

        Returns:
            Dictionary with certificate requirements and estimated cost
        """
        # Each certificate covers 1 tonne of CO2e
        certificates_required = net_emissions_tco2e.quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )

        # Fractional certificates are allowed
        fractional_certificates = net_emissions_tco2e.quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

        # Estimated cost
        estimated_cost = (fractional_certificates * eu_ets_price_eur).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "net_emissions_tco2e": net_emissions_tco2e,
            "certificates_required": int(certificates_required),
            "fractional_certificates": fractional_certificates,
            "eu_ets_price_eur": eu_ets_price_eur,
            "estimated_cost_eur": estimated_cost,
        }

    def calculate_import_full(
        self,
        cn_code: str,
        mass_tonnes: Decimal,
        country_code: str,
        actual_direct_see: Optional[Decimal] = None,
        actual_indirect_see: Optional[Decimal] = None,
        electricity_consumption_mwh: Optional[Decimal] = None,
        foreign_carbon_price_eur: Optional[Decimal] = None,
        foreign_free_allocation_pct: Decimal = Decimal("0"),
        eu_ets_price_eur: Decimal = Decimal("80"),
        eu_free_allocation_pct: Decimal = Decimal("0"),
        is_definitive_phase: bool = False,
    ) -> dict:
        """
        Perform full CBAM calculation for an import.

        This combines all calculation steps:
        1. Calculate embedded emissions
        2. Apply carbon price deductions
        3. Calculate certificate requirements (if definitive phase)

        Args:
            cn_code: CN code for the product
            mass_tonnes: Mass of imported product in tonnes
            country_code: ISO country code of production facility
            actual_direct_see: Actual direct SEE from installation
            actual_indirect_see: Actual indirect SEE from installation
            electricity_consumption_mwh: Actual electricity consumption
            foreign_carbon_price_eur: Carbon price paid in country of origin
            foreign_free_allocation_pct: Free allocation in foreign country
            eu_ets_price_eur: Current EU ETS price
            eu_free_allocation_pct: EU free allocation for this sector
            is_definitive_phase: Whether to calculate certificate requirements

        Returns:
            Comprehensive dictionary with all calculation results
        """
        # Step 1: Calculate embedded emissions
        emissions = self.calculate_embedded_emissions(
            cn_code=cn_code,
            mass_tonnes=mass_tonnes,
            country_code=country_code,
            actual_direct_see=actual_direct_see,
            actual_indirect_see=actual_indirect_see,
            electricity_consumption_mwh=electricity_consumption_mwh,
        )

        # Step 2: Calculate carbon price deduction
        deduction = self.calculate_carbon_price_deduction(
            total_emissions_tco2e=emissions["total_emissions_tco2e"],
            foreign_carbon_price_eur=foreign_carbon_price_eur,
            foreign_free_allocation_pct=foreign_free_allocation_pct,
            eu_ets_price_eur=eu_ets_price_eur,
            eu_free_allocation_pct=eu_free_allocation_pct,
        )

        # Step 3: Calculate certificate requirements (definitive phase only)
        certificates = None
        if is_definitive_phase:
            certificates = self.calculate_certificate_requirement(
                net_emissions_tco2e=deduction["net_emissions_tco2e"],
                eu_ets_price_eur=eu_ets_price_eur,
            )

        # Get sector info
        sector = get_sector_for_cn_code(cn_code)

        return {
            "summary": {
                "cn_code": cn_code,
                "sector": sector,
                "mass_tonnes": mass_tonnes,
                "country_code": country_code,
                "total_emissions_tco2e": emissions["total_emissions_tco2e"],
                "net_emissions_tco2e": deduction["net_emissions_tco2e"],
                "net_cbam_cost_eur": deduction["net_cbam_cost_eur"],
                "calculation_method": emissions["calculation_method"],
                "is_definitive_phase": is_definitive_phase,
            },
            "embedded_emissions": emissions,
            "carbon_price_deduction": deduction,
            "certificate_requirement": certificates,
            "warnings": emissions["warnings"],
        }


def aggregate_quarterly_report(
    imports: list[dict],
    quarter: int,
    year: int,
) -> dict:
    """
    Aggregate CBAM data for quarterly transitional reporting.

    During the transitional period (2024-2025), importers must submit
    quarterly reports with aggregated emissions by sector and CN code.

    Args:
        imports: List of import calculation results
        quarter: Quarter number (1-4)
        year: Reporting year

    Returns:
        Aggregated quarterly report data
    """
    from collections import defaultdict

    # Aggregate by sector
    by_sector = defaultdict(lambda: {
        "mass_tonnes": Decimal("0"),
        "direct_emissions_tco2e": Decimal("0"),
        "indirect_emissions_tco2e": Decimal("0"),
        "total_emissions_tco2e": Decimal("0"),
        "import_count": 0,
        "cn_codes": set(),
        "countries": set(),
    })

    # Aggregate by CN code
    by_cn_code = defaultdict(lambda: {
        "mass_tonnes": Decimal("0"),
        "total_emissions_tco2e": Decimal("0"),
        "import_count": 0,
        "countries": set(),
    })

    total_mass = Decimal("0")
    total_emissions = Decimal("0")

    for imp in imports:
        summary = imp.get("summary", imp)
        emissions = imp.get("embedded_emissions", imp)

        sector = summary.get("sector", "unknown")
        cn_code = summary.get("cn_code", "")
        country = summary.get("country_code", "")
        mass = summary.get("mass_tonnes", Decimal("0"))

        direct_em = emissions.get("direct_emissions_tco2e", Decimal("0"))
        indirect_em = emissions.get("indirect_emissions_tco2e", Decimal("0"))
        total_em = emissions.get("total_emissions_tco2e", Decimal("0"))

        # Sector aggregation
        by_sector[sector]["mass_tonnes"] += mass
        by_sector[sector]["direct_emissions_tco2e"] += direct_em
        by_sector[sector]["indirect_emissions_tco2e"] += indirect_em
        by_sector[sector]["total_emissions_tco2e"] += total_em
        by_sector[sector]["import_count"] += 1
        by_sector[sector]["cn_codes"].add(cn_code)
        by_sector[sector]["countries"].add(country)

        # CN code aggregation
        by_cn_code[cn_code]["mass_tonnes"] += mass
        by_cn_code[cn_code]["total_emissions_tco2e"] += total_em
        by_cn_code[cn_code]["import_count"] += 1
        by_cn_code[cn_code]["countries"].add(country)

        total_mass += mass
        total_emissions += total_em

    # Convert sets to lists for JSON serialization
    sector_summary = {}
    for sector, data in by_sector.items():
        sector_summary[sector] = {
            **data,
            "cn_codes": list(data["cn_codes"]),
            "countries": list(data["countries"]),
        }

    cn_code_summary = {}
    for cn, data in by_cn_code.items():
        cn_code_summary[cn] = {
            **data,
            "countries": list(data["countries"]),
        }

    return {
        "report_period": {
            "quarter": quarter,
            "year": year,
            "period_type": "transitional" if year <= 2025 else "definitive",
        },
        "totals": {
            "import_count": len(imports),
            "mass_tonnes": total_mass,
            "total_emissions_tco2e": total_emissions,
            "sector_count": len(by_sector),
        },
        "by_sector": sector_summary,
        "by_cn_code": cn_code_summary,
    }


def aggregate_annual_declaration(
    imports: list[dict],
    year: int,
    eu_ets_prices: list[dict],
) -> dict:
    """
    Aggregate CBAM data for annual declaration (definitive phase from 2026).

    Annual declarations require:
    - Total embedded emissions by sector
    - Certificate surrender calculations
    - Carbon price deductions claimed

    Args:
        imports: List of import calculation results (full calculations)
        year: Declaration year
        eu_ets_prices: Weekly EU ETS prices for the year

    Returns:
        Annual declaration data with certificate requirements
    """
    from collections import defaultdict

    # Calculate average ETS price for the year
    if eu_ets_prices:
        avg_ets_price = sum(
            Decimal(str(p.get("price_eur", 80))) for p in eu_ets_prices
        ) / len(eu_ets_prices)
    else:
        avg_ets_price = Decimal("80")

    # Aggregate totals
    total_gross_emissions = Decimal("0")
    total_net_emissions = Decimal("0")
    total_deductions = Decimal("0")
    total_certificates = Decimal("0")
    total_cost = Decimal("0")

    by_sector = defaultdict(lambda: {
        "gross_emissions_tco2e": Decimal("0"),
        "net_emissions_tco2e": Decimal("0"),
        "certificates_required": Decimal("0"),
        "estimated_cost_eur": Decimal("0"),
    })

    for imp in imports:
        summary = imp.get("summary", {})
        deduction = imp.get("carbon_price_deduction", {})
        certs = imp.get("certificate_requirement", {})

        sector = summary.get("sector", "unknown")
        gross_em = summary.get("total_emissions_tco2e", Decimal("0"))
        net_em = deduction.get("net_emissions_tco2e", Decimal("0"))
        deduction_em = deduction.get("deduction_tco2e", Decimal("0"))

        cert_count = Decimal(str(certs.get("fractional_certificates", net_em))) if certs else net_em
        cert_cost = Decimal(str(certs.get("estimated_cost_eur", net_em * avg_ets_price))) if certs else net_em * avg_ets_price

        total_gross_emissions += gross_em
        total_net_emissions += net_em
        total_deductions += deduction_em
        total_certificates += cert_count
        total_cost += cert_cost

        by_sector[sector]["gross_emissions_tco2e"] += gross_em
        by_sector[sector]["net_emissions_tco2e"] += net_em
        by_sector[sector]["certificates_required"] += cert_count
        by_sector[sector]["estimated_cost_eur"] += cert_cost

    return {
        "declaration_year": year,
        "declaration_type": "definitive",
        "average_ets_price_eur": avg_ets_price.quantize(Decimal("0.01")),
        "totals": {
            "import_count": len(imports),
            "gross_emissions_tco2e": total_gross_emissions.quantize(Decimal("0.001")),
            "deductions_tco2e": total_deductions.quantize(Decimal("0.001")),
            "net_emissions_tco2e": total_net_emissions.quantize(Decimal("0.001")),
            "certificates_required": total_certificates.quantize(Decimal("0.001")),
            "estimated_total_cost_eur": total_cost.quantize(Decimal("0.01")),
        },
        "by_sector": dict(by_sector),
    }
