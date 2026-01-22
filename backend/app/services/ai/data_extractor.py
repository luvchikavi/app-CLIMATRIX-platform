"""
Data Extractor - AI-powered extraction of emission data from unstructured content.

Extracts structured emission data from:
- Messy Excel cells with mixed content
- Free-text descriptions
- Invoice/receipt text
- Multi-language inputs
"""
import json
import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.services.ai.claude_service import ClaudeService


@dataclass
class ExtractedActivity:
    """Single extracted activity from unstructured data."""
    activity_key: str
    quantity: Decimal
    unit: str
    description: str
    scope: int
    category_code: str
    confidence: float  # 0.0 to 1.0
    source_text: str  # Original text this was extracted from
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Complete extraction result."""
    success: bool
    activities: list[ExtractedActivity]
    unmatched_text: list[str]  # Parts that couldn't be extracted
    warnings: list[str]
    ai_notes: Optional[str] = None


class DataExtractor:
    """
    Extracts structured emission data from unstructured text.

    Handles complex cases like:
    - "We used 1,500 m³ of natural gas and 25,000 kWh electricity this month"
    - "Diesel fuel: 2500L @ $1.50/L"
    - "Flight TLV→LHR return x 3 employees"
    - "Waste disposal: 500kg general, 200kg recycling"

    Usage:
        extractor = DataExtractor()
        result = extractor.extract(
            "Natural gas consumption: 1,234.5 m³ in January"
        )
    """

    EXTRACTION_PROMPT = """Extract emission activity data from this text.

For each activity found, provide:
1. The activity_key (from CLIMATRIX activity types)
2. The quantity (as a number)
3. The unit
4. A clean description
5. The GHG scope (1, 2, or 3)
6. The category code
7. Your confidence level (0.0-1.0)

Text to analyze:
{text}

Respond with this JSON structure:
{{
    "activities": [
        {{
            "activity_key": "string",
            "quantity": number,
            "unit": "string",
            "description": "clean description",
            "scope": 1|2|3,
            "category_code": "string",
            "confidence": 0.0-1.0,
            "source_text": "the part of text this came from"
        }}
    ],
    "unmatched_text": ["parts that couldn't be matched"],
    "warnings": ["any data quality warnings"],
    "notes": "any helpful notes"
}}

If no emission activities are found, return empty activities array.
Be careful with units - distinguish between m³ (cubic meters), m3, m (meters)."""

    def __init__(self, claude_service: Optional[ClaudeService] = None):
        """Initialize with Claude service."""
        self.claude = claude_service or ClaudeService()

    def extract(self, text: str) -> ExtractionResult:
        """
        Extract emission activities from unstructured text.

        Args:
            text: Unstructured text potentially containing emission data

        Returns:
            ExtractionResult with extracted activities
        """
        if not text or not text.strip():
            return ExtractionResult(
                success=True,
                activities=[],
                unmatched_text=[],
                warnings=["Empty text provided"],
            )

        # Try AI extraction first
        if self.claude.is_available():
            return self._ai_extract(text)

        # Fall back to regex extraction
        return self._regex_extract(text)

    def _ai_extract(self, text: str) -> ExtractionResult:
        """Use Claude AI to extract data."""
        prompt = self.EXTRACTION_PROMPT.format(text=text)
        response = self.claude.analyze(prompt, json_response=True)

        if not response.success:
            return self._regex_extract(text)

        try:
            data = response.content
            activities = [
                ExtractedActivity(
                    activity_key=a["activity_key"],
                    quantity=Decimal(str(a["quantity"])),
                    unit=a["unit"],
                    description=a["description"],
                    scope=a["scope"],
                    category_code=a["category_code"],
                    confidence=a.get("confidence", 0.8),
                    source_text=a.get("source_text", ""),
                    warnings=[],
                )
                for a in data.get("activities", [])
            ]

            return ExtractionResult(
                success=True,
                activities=activities,
                unmatched_text=data.get("unmatched_text", []),
                warnings=data.get("warnings", []),
                ai_notes=data.get("notes"),
            )

        except (KeyError, TypeError, ValueError) as e:
            return self._regex_extract(text)

    def _regex_extract(self, text: str) -> ExtractionResult:
        """
        Regex-based fallback extraction.

        Handles common patterns when AI is not available.
        """
        activities = []
        warnings = []
        unmatched = []

        # Pattern: number + unit + activity keyword
        # Examples: "1500 m³ natural gas", "25000 kWh electricity"
        patterns = [
            # Natural gas
            (r'([\d,\.]+)\s*(m³|m3|cubic\s*meters?)\s*(?:of\s*)?(natural\s*gas|gas)',
             "natural_gas_volume", 1, "1.1", "m³"),

            # Electricity
            (r'([\d,\.]+)\s*(kwh|mwh|gwh)\s*(?:of\s*)?(electricity|electric|power)?',
             "electricity_global", 2, "2", "kWh"),

            # Diesel
            (r'([\d,\.]+)\s*(liters?|litres?|L|gallons?|gal)\s*(?:of\s*)?(diesel)',
             "diesel_volume", 1, "1.1", "liters"),

            # Petrol/Gasoline
            (r'([\d,\.]+)\s*(liters?|litres?|L|gallons?|gal)\s*(?:of\s*)?(petrol|gasoline)',
             "petrol_vehicle_liters", 1, "1.2", "liters"),

            # LPG
            (r'([\d,\.]+)\s*(liters?|litres?|L|kg)\s*(?:of\s*)?(lpg|propane)',
             "lpg_volume", 1, "1.1", "liters"),

            # Waste
            (r'([\d,\.]+)\s*(kg|tonnes?|tons?)\s*(?:of\s*)?(waste|garbage|refuse)',
             "waste_mixed_landfill", 3, "3.5", "kg"),

            # Distance (for vehicles)
            (r'([\d,\.]+)\s*(km|kilometers?|kilometres?|miles?|mi)\s*(?:driven|traveled|travelled)?',
             "petrol_vehicle_km", 1, "1.2", "km"),
        ]

        text_lower = text.lower()

        for pattern, activity_key, scope, category, default_unit in patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                try:
                    quantity_str = match.group(1).replace(",", "")
                    quantity = Decimal(quantity_str)
                    unit_found = match.group(2).lower()

                    # Normalize unit
                    unit = default_unit
                    if unit_found in ["kwh"]:
                        unit = "kWh"
                    elif unit_found in ["mwh"]:
                        unit = "MWh"
                        quantity = quantity * 1000  # Convert to kWh
                        unit = "kWh"
                    elif unit_found in ["m³", "m3", "cubic meters", "cubic meter"]:
                        unit = "m³"
                    elif unit_found in ["liters", "liter", "litres", "litre", "l"]:
                        unit = "liters"
                    elif unit_found in ["gallons", "gallon", "gal"]:
                        unit = "gallons"
                    elif unit_found in ["kg"]:
                        unit = "kg"
                    elif unit_found in ["tonnes", "tonne", "tons", "ton"]:
                        unit = "tonnes"
                    elif unit_found in ["km", "kilometers", "kilometres", "kilometer", "kilometre"]:
                        unit = "km"
                    elif unit_found in ["miles", "mile", "mi"]:
                        unit = "miles"

                    activities.append(ExtractedActivity(
                        activity_key=activity_key,
                        quantity=quantity,
                        unit=unit,
                        description=match.group(0),
                        scope=scope,
                        category_code=category,
                        confidence=0.6,
                        source_text=match.group(0),
                        warnings=["Extracted via regex pattern matching"],
                    ))
                except (ValueError, IndexError) as e:
                    warnings.append(f"Failed to parse: {match.group(0)}")

        if not activities:
            unmatched.append(text)
            warnings.append("No emission activities could be extracted")

        return ExtractionResult(
            success=True,
            activities=activities,
            unmatched_text=unmatched,
            warnings=warnings,
            ai_notes="Regex-based extraction (AI not available)",
        )

    def extract_from_rows(self, rows: list[dict]) -> list[ExtractionResult]:
        """
        Extract from multiple rows of data.

        Args:
            rows: List of row dictionaries

        Returns:
            List of extraction results
        """
        results = []
        for row in rows:
            # Combine all text values in the row
            text_parts = [str(v) for v in row.values() if v]
            combined_text = " | ".join(text_parts)
            result = self.extract(combined_text)
            results.append(result)
        return results
