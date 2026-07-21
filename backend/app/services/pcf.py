"""
PCF service — computes product carbon footprints per ISO 14067 / PACT
Methodology v3 and builds the PACT Data Exchange JSON.

Every BOM line resolves through the EXISTING calculation engine
(CalculationPipeline → FactorResolver with region precedence), so a PCF
line has the same grounding, formula and warnings story as a Smart Import
row. Supplier-PCF lines multiply directly (primary data on the PACT
ladder) and drive the primary-data-share metric.

Boundary is cradle-to-gate (the PACT B2B default). Offsets are never
included (PACT rule). Biogenic CO2 is reported separately, mirroring the
corporate lane. Conformance testing against the PACT ACT checker is a
follow-up once we exchange files with a real buyer system.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Organization, ReportingPeriod
from app.models.product import (
    Product,
    ProductInput,
    ProductInputType,
    SupplierPCF,
)
from app.services.calculation.pipeline import (
    ActivityInput,
    CalculationError,
    CalculationPipeline,
)
from app.services.calculation.resolver import FactorNotFoundError, base_factor_region

# Default GHGP category per BOM input type — picks the calculator strategy.
# Energy lines refine to 2.1 for electricity keys (grid factors) vs 1.1 fuels.
_TYPE_DEFAULTS = {
    ProductInputType.PURCHASED_MATERIAL.value: (3, "3.1"),
    ProductInputType.ENERGY.value: (1, "1.1"),
    ProductInputType.TRANSPORT.value: (3, "3.4"),
    ProductInputType.PROCESS.value: (1, "1.1"),
}

# EN 15804 module implied by input type (overridable per line).
TYPE_MODULE = {
    ProductInputType.PURCHASED_MATERIAL.value: "A1",
    ProductInputType.SUPPLIER_PCF.value: "A1",
    ProductInputType.TRANSPORT.value: "A2",
    ProductInputType.ENERGY.value: "A3",
    ProductInputType.PROCESS.value: "A3",
}


def _line_scope_category(line: ProductInput) -> tuple[int, str]:
    if line.scope and line.category_code:
        return line.scope, line.category_code
    scope, category = _TYPE_DEFAULTS.get(line.input_type, (3, "3.1"))
    if line.input_type == ProductInputType.ENERGY.value and (
        line.activity_key or ""
    ).startswith("electricity"):
        scope, category = 2, "2.1"
    return line.scope or scope, line.category_code or category


async def compute_footprint(
    session: AsyncSession,
    org: Organization,
    product: Product,
    period: ReportingPeriod,
    inputs: list[ProductInput],
    supplier_pcfs: dict,  # id -> SupplierPCF
) -> dict:
    """Compute the per-declared-unit footprint from the BOM.

    Returns a dict ready to persist on ProductFootprint: totals, stage
    breakdown, per-line derivation stories, primary-data share, warnings.
    Lines that cannot resolve a factor become honest gaps (contribution 0,
    warning recorded) rather than silent omissions.
    """
    pipeline = CalculationPipeline(session)
    default_region = base_factor_region(org)
    year = period.start_date.year if period.start_date else datetime.utcnow().year

    total = Decimal("0")
    biogenic_total = Decimal("0")
    primary = Decimal("0")
    stages: dict[str, Decimal] = {}
    lines: list[dict] = []
    warnings: list[str] = []

    for line in sorted(inputs, key=lambda i: (i.sort_order, i.created_at)):
        entry = {
            "input_id": str(line.id),
            "name": line.name,
            "input_type": line.input_type,
            "en15804_module": line.en15804_module
            or TYPE_MODULE.get(line.input_type, "A1"),
            "quantity_per_unit": float(line.quantity_per_unit),
            "unit": line.unit,
            "co2e_kg": 0.0,
            "biogenic_co2_kg": None,
            "is_primary_data": False,
            "status": "ok",
            "warnings": [],
        }

        if line.input_type == ProductInputType.SUPPLIER_PCF.value:
            spcf: Optional[SupplierPCF] = supplier_pcfs.get(line.supplier_pcf_id)
            if spcf is None:
                entry["status"] = "gap"
                entry["warnings"].append("Supplier PCF reference missing")
                warnings.append(f"{line.name}: supplier PCF reference missing")
            else:
                if spcf.unit.strip().lower() != line.unit.strip().lower():
                    entry["warnings"].append(
                        f"Unit mismatch: BOM line is per {line.unit}, supplier "
                        f"PCF is per {spcf.unit} — quantities multiplied as-is"
                    )
                co2e = line.quantity_per_unit * spcf.pcf_value
                entry["co2e_kg"] = float(co2e)
                entry["is_primary_data"] = True
                entry["factor"] = {
                    "source": f"Supplier PCF — {spcf.supplier_name}",
                    "display_name": spcf.product_name,
                    "value": float(spcf.pcf_value),
                    "unit": f"kg CO2e/{spcf.unit}",
                    "boundary": spcf.boundary,
                    "pact_pf_id": spcf.pact_pf_id,
                }
                entry["formula"] = (
                    f"{line.quantity_per_unit} {line.unit} × "
                    f"{spcf.pcf_value} kg CO2e/{spcf.unit} = {co2e} kg CO2e"
                )
                total += co2e
                primary += co2e
        elif not line.activity_key:
            entry["status"] = "gap"
            entry["warnings"].append("No emission factor selected for this input")
            warnings.append(f"{line.name}: no emission factor selected")
        else:
            scope, category = _line_scope_category(line)
            region = line.region or default_region
            try:
                result = await pipeline.calculate(
                    ActivityInput(
                        activity_key=line.activity_key,
                        quantity=line.quantity_per_unit,
                        unit=line.unit,
                        scope=scope,
                        category_code=category,
                        region=region,
                        year=year,
                    )
                )
            except (FactorNotFoundError, CalculationError) as exc:
                entry["status"] = "gap"
                entry["warnings"].append(str(exc))
                warnings.append(f"{line.name}: {exc}")
            else:
                entry["co2e_kg"] = float(result.co2e_kg)
                entry["biogenic_co2_kg"] = (
                    float(result.biogenic_co2_kg)
                    if result.biogenic_co2_kg is not None
                    else None
                )
                entry["factor"] = {
                    "source": result.factor_source,
                    "display_name": result.factor_display_name,
                    "value": float(result.factor_value),
                    "unit": result.factor_unit,
                    "region": result.factor_region,
                    "year": result.factor_year,
                    "resolution_strategy": result.resolution_strategy,
                    "confidence": result.confidence,
                }
                entry["formula"] = result.formula
                entry["warnings"].extend(result.warnings)
                total += result.co2e_kg
                if result.biogenic_co2_kg:
                    biogenic_total += result.biogenic_co2_kg

        stage = entry["en15804_module"]
        stages[stage] = stages.get(stage, Decimal("0")) + Decimal(str(entry["co2e_kg"]))
        lines.append(entry)

    primary_share = float(primary / total * 100) if total else None

    return {
        "total_kgco2e_per_unit": total,
        "fossil_kgco2e_per_unit": total,  # co2e excludes biogenic by design
        "biogenic_kgco2e_per_unit": biogenic_total if biogenic_total else None,
        "primary_data_share": primary_share,
        "stage_breakdown": {k: float(v) for k, v in sorted(stages.items())},
        "line_items": lines,
        "warnings": warnings,
        "methodology": {
            "standard": "ISO 14067:2018",
            "exchange": "PACT Methodology v3",
            "boundary": "cradle_to_gate",
            "gwp": "IPCC AR5 (100-year)",
            "allocation": "physical (per declared unit BOM)",
            "offsets_included": False,
            "factor_year": year,
        },
    }


# Our declared-unit vocabulary → PACT DeclaredUnit strings. Tonne exports as
# kilogram with the amount scaled ×1000 (PACT has no tonne unit).
_PACT_UNITS = {
    "kilogram": "kilogram",
    "tonne": "kilogram",
    "liter": "liter",
    "cubic_meter": "cubic meter",
    "kilowatt_hour": "kilowatt hour",
    "megajoule": "megajoule",
    "ton_kilometer": "ton kilometer",
    "square_meter": "square meter",
    "piece": "piece",
}


def _dec(value) -> str:
    """PACT serializes decimals as strings."""
    return str(Decimal(str(value)).normalize())


def build_pact_json(
    org: Organization, product: Product, footprint, period: ReportingPeriod
) -> dict:
    """Build the PACT Data Exchange (Tech Spec v3) ProductFootprint document."""
    unit = _PACT_UNITS.get(footprint.declared_unit, "piece")
    amount = Decimal(str(footprint.declared_unit_amount))
    pcf_value = Decimal(str(footprint.total_kgco2e_per_unit))
    if footprint.declared_unit == "tonne":
        amount = amount * 1000
        pcf_value = pcf_value / 1000  # per-kg once the unit is kilogram

    sources = sorted(
        {
            li.get("factor", {}).get("source")
            for li in (footprint.line_items or [])
            if li.get("factor", {}).get("source") and not li.get("is_primary_data")
        }
    )
    biogenic = footprint.biogenic_kgco2e_per_unit
    company_urn = f"urn:pact:company:climatrix:{org.id}"
    product_urn = f"urn:pact:product:sku:{product.sku or product.id}"

    return {
        "id": str(uuid4()),
        "specVersion": "3.0.1",
        "version": 0,
        "created": datetime.utcnow().isoformat() + "Z",
        "status": "Active",
        "companyName": org.name,
        "companyIds": [company_urn],
        "productDescription": product.description or product.name,
        "productIds": [product_urn],
        "productNameCompany": product.name,
        "comment": "Prepared with Climatrix — climatrix.co",
        "pcf": {
            "declaredUnitOfMeasurement": unit,
            "declaredUnitAmount": _dec(amount),
            "pcfExcludingBiogenic": _dec(pcf_value),
            "pcfIncludingBiogenic": (
                _dec(pcf_value + Decimal(str(biogenic))) if biogenic else None
            ),
            "fossilGhgEmissions": _dec(pcf_value),
            "biogenicCarbonContent": _dec(biogenic) if biogenic else "0",
            "ipccCharacterizationFactors": ["AR5"],
            "crossSectoralStandards": ["ISO 14067", "PACT Methodology 3.0"],
            "boundaryProcessesDescription": "Cradle-to-gate: raw material "
            "acquisition (A1), inbound transport (A2), own production (A3).",
            "referencePeriodStart": (
                f"{period.start_date.isoformat()}T00:00:00Z"
                if period.start_date
                else None
            ),
            "referencePeriodEnd": (
                f"{period.end_date.isoformat()}T23:59:59Z" if period.end_date else None
            ),
            "geographyCountry": org.country_code,
            "secondaryEmissionFactorSources": [
                {"source": s, "version": ""} for s in sources
            ],
            "exemptedEmissionsPercent": 0,
            "exemptedEmissionsDescription": "",
            "packagingEmissionsIncluded": False,
            "allocationRulesDescription": (footprint.methodology or {}).get(
                "allocation", "physical"
            ),
            "primaryDataShare": (
                round(footprint.primary_data_share, 2)
                if footprint.primary_data_share is not None
                else None
            ),
        },
        "extensions": [
            {
                "specVersion": "2.0.0",
                "dataSchema": "https://climatrix.co/schemas/pcf-provenance.json",
                "data": {
                    "stageBreakdownKgCO2e": footprint.stage_breakdown,
                    "warnings": footprint.warnings or [],
                },
            }
        ],
    }


def parse_supplier_pact_json(payload: dict) -> dict:
    """Validate + flatten an uploaded PACT ProductFootprint JSON into
    SupplierPCF fields. Raises ValueError with a readable message on bad files.
    Accepts both v2 (declaredUnit/unitaryProductAmount) and v3 field names.
    """
    if not isinstance(payload, dict):
        raise ValueError("Not a JSON object")
    pcf = payload.get("pcf")
    if not isinstance(pcf, dict):
        raise ValueError("Missing 'pcf' object — not a PACT ProductFootprint file")

    value = pcf.get("pcfExcludingBiogenic") or pcf.get("pcfExcludingBiogenicUptake")
    if value is None:
        raise ValueError("Missing pcfExcludingBiogenic value")
    try:
        value = Decimal(str(value))
    except ArithmeticError:
        raise ValueError(f"Invalid PCF value: {value!r}")

    unit = pcf.get("declaredUnitOfMeasurement") or pcf.get("declaredUnit")
    if not unit:
        raise ValueError("Missing declared unit")

    supplier = payload.get("companyName") or "Unknown supplier"
    product_name = (
        payload.get("productNameCompany")
        or payload.get("productDescription")
        or "Unknown product"
    )
    share = pcf.get("primaryDataShare")

    return {
        "supplier_name": str(supplier)[:255],
        "product_name": str(product_name)[:255],
        "pcf_value": value,
        "unit": str(unit)[:50],
        "boundary": "cradle_to_gate",
        "primary_data_share": float(share) if share is not None else None,
        "pact_pf_id": str(payload.get("id") or "")[:64] or None,
        "source": "pact_json",
        "raw_payload": payload,
    }
