"""
CBAM Export Service.

Generates export formats for CBAM reporting:
- EU Commission quarterly report format
- XML export for EU CBAM Registry submission
- CSV export for data analysis
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from xml.etree import ElementTree as ET
from xml.dom import minidom
import csv
import io

from app.models.cbam import (
    CBAMQuarterlyReport,
    CBAMImport,
    CBAMInstallation,
    CBAMSector,
)


def format_decimal(value: Optional[Decimal], places: int = 3) -> str:
    """Format decimal for export."""
    if value is None:
        return "0"
    return str(value.quantize(Decimal(10) ** -places))


class CBAMXMLExporter:
    """Generate XML exports for EU CBAM Registry submission."""

    # XML namespace for CBAM
    CBAM_NS = "urn:eu:ec:cbam:report:v1"
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

    def __init__(self):
        """Initialize the exporter."""
        pass

    def generate_quarterly_xml(
        self,
        report: dict,
        imports: List[dict],
        installations: List[dict],
        declarant: dict,
    ) -> str:
        """
        Generate XML for quarterly CBAM report submission.

        Args:
            report: Quarterly report data
            imports: List of import records for the quarter
            installations: List of installation data
            declarant: Declarant (importer) information

        Returns:
            XML string formatted for EU CBAM Registry
        """
        # Create root element with namespaces
        root = ET.Element("CBAMQuarterlyReport")
        root.set("xmlns", self.CBAM_NS)
        root.set("xmlns:xsi", self.XSI_NS)

        # Report header
        header = ET.SubElement(root, "ReportHeader")
        ET.SubElement(header, "ReportingYear").text = str(report.get("year", date.today().year))
        ET.SubElement(header, "ReportingQuarter").text = str(report.get("quarter", 1))
        ET.SubElement(header, "SubmissionDate").text = datetime.utcnow().isoformat()
        ET.SubElement(header, "ReportVersion").text = "1"

        # Declarant information
        declarant_elem = ET.SubElement(root, "Declarant")
        ET.SubElement(declarant_elem, "Name").text = declarant.get("name", "")
        ET.SubElement(declarant_elem, "EORI").text = declarant.get("eori", "")
        ET.SubElement(declarant_elem, "Address").text = declarant.get("address", "")
        ET.SubElement(declarant_elem, "Country").text = declarant.get("country", "")

        # Installations
        installations_elem = ET.SubElement(root, "Installations")
        installation_map = {str(inst.get("id")): inst for inst in installations}

        for inst in installations:
            inst_elem = ET.SubElement(installations_elem, "Installation")
            ET.SubElement(inst_elem, "InstallationID").text = str(inst.get("id", ""))
            ET.SubElement(inst_elem, "Name").text = inst.get("name", "")
            ET.SubElement(inst_elem, "Country").text = inst.get("country_code", "")
            ET.SubElement(inst_elem, "Address").text = inst.get("address", "")

            # Installation-level emissions data
            inst_emissions = ET.SubElement(inst_elem, "EmissionsData")
            ET.SubElement(inst_emissions, "DirectEmissionsFactor").text = "0"
            ET.SubElement(inst_emissions, "IndirectEmissionsFactor").text = "0"
            ET.SubElement(inst_emissions, "VerificationStatus").text = inst.get("verification_status", "pending")

        # Goods (imports)
        goods_elem = ET.SubElement(root, "ImportedGoods")

        for imp in imports:
            good = ET.SubElement(goods_elem, "Good")
            ET.SubElement(good, "GoodID").text = str(imp.get("id", ""))
            ET.SubElement(good, "CNCode").text = imp.get("cn_code", "")
            ET.SubElement(good, "Description").text = imp.get("product_description", "")

            # Quantities
            qty = ET.SubElement(good, "Quantity")
            ET.SubElement(qty, "Mass").text = format_decimal(imp.get("mass_tonnes"))
            ET.SubElement(qty, "Unit").text = "tonnes"

            # Origin
            origin = ET.SubElement(good, "Origin")
            inst_id = str(imp.get("installation_id", ""))
            installation = installation_map.get(inst_id, {})
            ET.SubElement(origin, "InstallationRef").text = inst_id
            ET.SubElement(origin, "Country").text = installation.get("country_code", "")

            # Embedded emissions
            emissions = ET.SubElement(good, "EmbeddedEmissions")
            ET.SubElement(emissions, "DirectEmissions").text = format_decimal(imp.get("direct_emissions_tco2e"))
            ET.SubElement(emissions, "IndirectEmissions").text = format_decimal(imp.get("indirect_emissions_tco2e"))
            ET.SubElement(emissions, "TotalEmissions").text = format_decimal(imp.get("total_emissions_tco2e"))
            ET.SubElement(emissions, "CalculationMethod").text = imp.get("calculation_method", "default")

            # SEE (Specific Embedded Emissions)
            see = ET.SubElement(good, "SpecificEmbeddedEmissions")
            ET.SubElement(see, "DirectSEE").text = format_decimal(imp.get("direct_see"))
            ET.SubElement(see, "IndirectSEE").text = format_decimal(imp.get("indirect_see"))
            ET.SubElement(see, "TotalSEE").text = format_decimal(imp.get("total_see"))

            # Carbon price paid (if any)
            if imp.get("foreign_carbon_price_eur"):
                carbon_price = ET.SubElement(good, "CarbonPricePaid")
                ET.SubElement(carbon_price, "Amount").text = format_decimal(imp.get("foreign_carbon_price_eur"), 2)
                ET.SubElement(carbon_price, "Currency").text = imp.get("foreign_carbon_price_currency", "EUR")

        # Summary totals
        summary = ET.SubElement(root, "Summary")
        ET.SubElement(summary, "TotalImports").text = str(report.get("total_imports", len(imports)))
        ET.SubElement(summary, "TotalMassTonnes").text = format_decimal(report.get("total_mass_tonnes"))
        ET.SubElement(summary, "TotalDirectEmissions").text = format_decimal(
            sum(Decimal(str(imp.get("direct_emissions_tco2e", 0))) for imp in imports)
        )
        ET.SubElement(summary, "TotalIndirectEmissions").text = format_decimal(
            sum(Decimal(str(imp.get("indirect_emissions_tco2e", 0))) for imp in imports)
        )
        ET.SubElement(summary, "TotalEmissions").text = format_decimal(report.get("total_emissions_tco2e"))

        # By sector summary
        by_sector_elem = ET.SubElement(summary, "BySector")
        for sector, data in (report.get("by_sector") or {}).items():
            sector_elem = ET.SubElement(by_sector_elem, "Sector")
            ET.SubElement(sector_elem, "SectorCode").text = sector
            ET.SubElement(sector_elem, "MassTonnes").text = format_decimal(data.get("mass_tonnes"))
            ET.SubElement(sector_elem, "TotalEmissions").text = format_decimal(data.get("total_emissions_tco2e"))

        # Pretty print
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")

    def generate_annual_xml(
        self,
        declaration: dict,
        imports: List[dict],
        installations: List[dict],
        declarant: dict,
    ) -> str:
        """
        Generate XML for annual CBAM declaration (definitive phase).

        Args:
            declaration: Annual declaration data
            imports: List of import records for the year
            installations: List of installation data
            declarant: Declarant information

        Returns:
            XML string for EU CBAM Registry
        """
        root = ET.Element("CBAMAnnualDeclaration")
        root.set("xmlns", self.CBAM_NS)
        root.set("xmlns:xsi", self.XSI_NS)

        # Declaration header
        header = ET.SubElement(root, "DeclarationHeader")
        ET.SubElement(header, "DeclarationYear").text = str(declaration.get("year", date.today().year))
        ET.SubElement(header, "SubmissionDate").text = datetime.utcnow().isoformat()
        ET.SubElement(header, "DeclarationType").text = "annual"

        # Declarant
        declarant_elem = ET.SubElement(root, "Declarant")
        ET.SubElement(declarant_elem, "Name").text = declarant.get("name", "")
        ET.SubElement(declarant_elem, "EORI").text = declarant.get("eori", "")
        ET.SubElement(declarant_elem, "AuthorisedDeclarantNumber").text = declarant.get("auth_number", "")

        # Certificate requirements
        certs = ET.SubElement(root, "CertificateRequirement")
        ET.SubElement(certs, "GrossEmissions").text = format_decimal(declaration.get("gross_emissions_tco2e"))
        ET.SubElement(certs, "Deductions").text = format_decimal(declaration.get("deductions_tco2e"))
        ET.SubElement(certs, "NetEmissions").text = format_decimal(declaration.get("net_emissions_tco2e"))
        ET.SubElement(certs, "CertificatesRequired").text = format_decimal(declaration.get("certificates_required"))
        ET.SubElement(certs, "EstimatedCostEUR").text = format_decimal(declaration.get("estimated_cost_eur"), 2)

        # Emissions by sector
        by_sector = ET.SubElement(root, "EmissionsBySector")
        for sector, data in (declaration.get("by_sector") or {}).items():
            sector_elem = ET.SubElement(by_sector, "Sector")
            ET.SubElement(sector_elem, "SectorCode").text = sector
            ET.SubElement(sector_elem, "GrossEmissions").text = format_decimal(data.get("gross_emissions_tco2e"))
            ET.SubElement(sector_elem, "NetEmissions").text = format_decimal(data.get("net_emissions_tco2e"))
            ET.SubElement(sector_elem, "Certificates").text = format_decimal(data.get("certificates_required"))

        # Pretty print
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")


class CBAMCSVExporter:
    """Generate CSV exports for CBAM data analysis."""

    def generate_imports_csv(self, imports: List[dict]) -> str:
        """
        Generate CSV of import records.

        Args:
            imports: List of import records

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Import ID",
            "CN Code",
            "Sector",
            "Description",
            "Import Date",
            "Mass (tonnes)",
            "Direct SEE (tCO2e/t)",
            "Indirect SEE (tCO2e/t)",
            "Total SEE (tCO2e/t)",
            "Direct Emissions (tCO2e)",
            "Indirect Emissions (tCO2e)",
            "Total Emissions (tCO2e)",
            "Calculation Method",
            "Foreign Carbon Price (EUR)",
            "Installation ID",
        ])

        # Data rows
        for imp in imports:
            writer.writerow([
                imp.get("id", ""),
                imp.get("cn_code", ""),
                imp.get("sector", ""),
                imp.get("product_description", ""),
                imp.get("import_date", ""),
                format_decimal(imp.get("mass_tonnes")),
                format_decimal(imp.get("direct_see")),
                format_decimal(imp.get("indirect_see")),
                format_decimal(imp.get("total_see")),
                format_decimal(imp.get("direct_emissions_tco2e")),
                format_decimal(imp.get("indirect_emissions_tco2e")),
                format_decimal(imp.get("total_emissions_tco2e")),
                imp.get("calculation_method", ""),
                format_decimal(imp.get("foreign_carbon_price_eur"), 2) if imp.get("foreign_carbon_price_eur") else "",
                imp.get("installation_id", ""),
            ])

        return output.getvalue()

    def generate_quarterly_summary_csv(self, report: dict) -> str:
        """
        Generate CSV summary of quarterly report.

        Args:
            report: Quarterly report data

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Summary section
        writer.writerow(["CBAM Quarterly Report Summary"])
        writer.writerow(["Year", report.get("year", "")])
        writer.writerow(["Quarter", report.get("quarter", "")])
        writer.writerow(["Status", report.get("status", "")])
        writer.writerow([])

        writer.writerow(["Total Imports", report.get("total_imports", 0)])
        writer.writerow(["Total Mass (tonnes)", format_decimal(report.get("total_mass_tonnes"))])
        writer.writerow(["Total Emissions (tCO2e)", format_decimal(report.get("total_emissions_tco2e"))])
        writer.writerow([])

        # By sector
        writer.writerow(["Breakdown by Sector"])
        writer.writerow(["Sector", "Import Count", "Mass (tonnes)", "Direct Emissions", "Indirect Emissions", "Total Emissions"])

        for sector, data in (report.get("by_sector") or {}).items():
            writer.writerow([
                sector,
                data.get("import_count", 0),
                format_decimal(data.get("mass_tonnes")),
                format_decimal(data.get("direct_emissions_tco2e")),
                format_decimal(data.get("indirect_emissions_tco2e")),
                format_decimal(data.get("total_emissions_tco2e")),
            ])

        return output.getvalue()


class CBAMReportFormatter:
    """Format CBAM reports in EU Commission style."""

    def format_quarterly_report(
        self,
        report: dict,
        imports: List[dict],
        installations: List[dict],
        organization: dict,
    ) -> dict:
        """
        Format quarterly report in EU Commission structure.

        Returns structured data matching EU Commission reporting requirements.
        """
        year = report.get("year", date.today().year)
        quarter = report.get("quarter", 1)

        # Calculate quarter dates
        quarter_start_month = (quarter - 1) * 3 + 1
        quarter_end_month = quarter * 3

        return {
            "report_type": "CBAM Quarterly Report",
            "regulation_reference": "EU Regulation 2023/956",
            "reporting_period": {
                "year": year,
                "quarter": quarter,
                "start_date": f"{year}-{quarter_start_month:02d}-01",
                "end_date": f"{year}-{quarter_end_month:02d}-{28 if quarter_end_month == 2 else 30 if quarter_end_month in [4, 6, 9, 11] else 31}",
                "phase": "transitional" if year <= 2025 else "definitive",
            },
            "reporting_declarant": {
                "name": organization.get("name", ""),
                "eori_number": organization.get("eori", ""),
                "address": organization.get("address", ""),
                "member_state": organization.get("country_code", ""),
            },
            "summary": {
                "total_imports": report.get("total_imports", 0),
                "total_mass_tonnes": float(report.get("total_mass_tonnes", 0)),
                "total_embedded_emissions_tco2e": float(report.get("total_emissions_tco2e", 0)),
                "direct_emissions_tco2e": sum(
                    float(imp.get("direct_emissions_tco2e", 0)) for imp in imports
                ),
                "indirect_emissions_tco2e": sum(
                    float(imp.get("indirect_emissions_tco2e", 0)) for imp in imports
                ),
            },
            "emissions_by_sector": {
                sector: {
                    "mass_tonnes": float(data.get("mass_tonnes", 0)),
                    "direct_emissions_tco2e": float(data.get("direct_emissions_tco2e", 0)),
                    "indirect_emissions_tco2e": float(data.get("indirect_emissions_tco2e", 0)),
                    "total_emissions_tco2e": float(data.get("total_emissions_tco2e", 0)),
                    "import_count": data.get("import_count", 0),
                    "cn_codes": data.get("cn_codes", []),
                    "source_countries": data.get("countries", []),
                }
                for sector, data in (report.get("by_sector") or {}).items()
            },
            "emissions_by_cn_code": {
                cn: {
                    "mass_tonnes": float(data.get("mass_tonnes", 0)),
                    "total_emissions_tco2e": float(data.get("total_emissions_tco2e", 0)),
                    "import_count": data.get("import_count", 0),
                    "source_countries": data.get("countries", []),
                }
                for cn, data in (report.get("by_cn_code") or {}).items()
            },
            "installations": [
                {
                    "id": str(inst.get("id", "")),
                    "name": inst.get("name", ""),
                    "country": inst.get("country_code", ""),
                    "sectors": inst.get("sectors", []),
                    "verification_status": inst.get("verification_status", "pending"),
                }
                for inst in installations
            ],
            "data_quality_notes": {
                "calculation_methods_used": list(set(imp.get("calculation_method", "default") for imp in imports)),
                "default_values_used": any(imp.get("calculation_method") == "default" for imp in imports),
                "actual_values_available": any(imp.get("calculation_method") == "actual" for imp in imports),
            },
            "submission_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "status": report.get("status", "draft"),
                "submitted_at": report.get("submitted_at"),
            },
        }
