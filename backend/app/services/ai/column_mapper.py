"""
Column Mapper - AI-powered mapping of Excel/CSV columns to activity_keys.

This is the key component for intelligent file imports. It uses Claude to:
1. Understand column headers (even in different languages)
2. Map to the correct activity_key
3. Detect the appropriate unit
4. Identify date and description columns
"""
import json
from dataclasses import dataclass
from typing import Optional

from app.services.ai.claude_service import ClaudeService


@dataclass
class ColumnMapping:
    """Result of mapping a single column."""
    original_header: str
    activity_key: Optional[str]
    scope: Optional[int]
    category_code: Optional[str]
    detected_unit: Optional[str]
    column_type: str  # "activity", "quantity", "unit", "date", "description", "ignore"
    confidence: float  # 0.0 to 1.0
    notes: Optional[str] = None


@dataclass
class MappingResult:
    """Complete mapping result for a file."""
    success: bool
    mappings: list[ColumnMapping]
    detected_structure: str  # "single_activity", "multi_activity", "pivot"
    quantity_column: Optional[str]
    unit_column: Optional[str]
    date_column: Optional[str]
    description_column: Optional[str]
    warnings: list[str]
    ai_notes: Optional[str] = None


class ColumnMapper:
    """
    Maps file columns to CLIMATRIX activity_keys using Claude AI.

    Handles various file structures:
    - Simple: One activity per row with quantity/unit columns
    - Multi-activity: Multiple activity columns (e.g., Electricity, Gas, Water)
    - Pivot: Activities as columns, dates as rows

    Usage:
        mapper = ColumnMapper()
        result = mapper.map_columns(
            headers=["Date", "Natural Gas (m³)", "Electricity (kWh)", "Notes"],
            sample_data=[["2024-01", "1500", "25000", "Office building"]]
        )
    """

    MAPPING_PROMPT = """Analyze these Excel/CSV column headers and map them to CLIMATRIX emission activity types.

For each column, determine:
1. What type of data it contains (activity quantity, unit, date, description, or ignore)
2. If it's an activity, which activity_key it maps to
3. The detected unit (if embedded in header like "Gas (m³)" or in data)
4. Your confidence level (0.0-1.0)

Also identify the overall file structure:
- "single_activity": One activity type per row, with activity_key in a column
- "multi_activity": Multiple activities as separate columns (most common)
- "pivot": Dates as rows, activities as columns

Column headers: {headers}
Sample data rows: {sample_data}

Respond with this exact JSON structure:
{{
    "detected_structure": "single_activity" | "multi_activity" | "pivot",
    "quantity_column": "column name if separate quantity column exists",
    "unit_column": "column name if separate unit column exists",
    "date_column": "column name for dates",
    "description_column": "column name for descriptions/notes",
    "mappings": [
        {{
            "original_header": "exact header text",
            "activity_key": "matched activity_key or null",
            "scope": 1 | 2 | 3 | null,
            "category_code": "1.1" | "2" | "3.5" | etc | null,
            "detected_unit": "kWh" | "liters" | "m³" | etc | null,
            "column_type": "activity" | "quantity" | "unit" | "date" | "description" | "ignore",
            "confidence": 0.0-1.0,
            "notes": "any important notes about this mapping"
        }}
    ],
    "warnings": ["list of any data quality warnings"],
    "notes": "overall analysis notes"
}}"""

    def __init__(self, claude_service: Optional[ClaudeService] = None):
        """Initialize with Claude service."""
        self.claude = claude_service or ClaudeService()

    def map_columns(
        self,
        headers: list[str],
        sample_data: Optional[list[list]] = None,
    ) -> MappingResult:
        """
        Map file columns to activity_keys.

        Args:
            headers: List of column header strings
            sample_data: Optional sample rows to help with detection

        Returns:
            MappingResult with all column mappings
        """
        # Try AI mapping first
        if self.claude.is_available():
            return self._ai_map_columns(headers, sample_data)

        # Fall back to rule-based mapping
        return self._rule_based_map(headers)

    def _ai_map_columns(
        self,
        headers: list[str],
        sample_data: Optional[list[list]] = None,
    ) -> MappingResult:
        """Use Claude to intelligently map columns."""
        prompt = self.MAPPING_PROMPT.format(
            headers=json.dumps(headers),
            sample_data=json.dumps(sample_data[:5] if sample_data else []),
        )

        response = self.claude.analyze(prompt, json_response=True)

        if not response.success:
            # Fall back to rule-based mapping
            return self._rule_based_map(headers)

        try:
            data = response.content
            mappings = [
                ColumnMapping(
                    original_header=m["original_header"],
                    activity_key=m.get("activity_key"),
                    scope=m.get("scope"),
                    category_code=m.get("category_code"),
                    detected_unit=m.get("detected_unit"),
                    column_type=m.get("column_type", "ignore"),
                    confidence=m.get("confidence", 0.5),
                    notes=m.get("notes"),
                )
                for m in data.get("mappings", [])
            ]

            return MappingResult(
                success=True,
                mappings=mappings,
                detected_structure=data.get("detected_structure", "multi_activity"),
                quantity_column=data.get("quantity_column"),
                unit_column=data.get("unit_column"),
                date_column=data.get("date_column"),
                description_column=data.get("description_column"),
                warnings=data.get("warnings", []),
                ai_notes=data.get("notes"),
            )

        except (KeyError, TypeError) as e:
            # Fall back to rule-based if parsing fails
            return self._rule_based_map(headers)

    def _rule_based_map(self, headers: list[str]) -> MappingResult:
        """
        Rule-based fallback mapping when AI is not available.

        Uses keyword matching for common patterns.
        """
        mappings = []
        date_column = None
        quantity_column = None
        unit_column = None
        description_column = None
        warnings = []

        # Keyword patterns for activity detection
        ACTIVITY_PATTERNS = {
            # Scope 1 - Fuels
            "natural gas": ("natural_gas_volume", 1, "1.1", "m³"),
            "gas usage": ("natural_gas_volume", 1, "1.1", "m³"),
            "diesel": ("diesel_volume", 1, "1.1", "liters"),
            "petrol": ("petrol_vehicle_liters", 1, "1.2", "liters"),
            "gasoline": ("petrol_vehicle_liters", 1, "1.2", "liters"),
            "lpg": ("lpg_volume", 1, "1.1", "liters"),
            "coal": ("coal_mass", 1, "1.1", "kg"),
            "refrigerant": ("refrigerant_r134a", 1, "1.3", "kg"),
            "r-134a": ("refrigerant_r134a", 1, "1.3", "kg"),
            "r-410a": ("refrigerant_r410a", 1, "1.3", "kg"),
            "sf6": ("sf6_leakage", 1, "1.3", "kg"),

            # Scope 2 - Electricity
            "electricity": ("electricity_global", 2, "2", "kWh"),
            "electric": ("electricity_global", 2, "2", "kWh"),
            "power": ("electricity_global", 2, "2", "kWh"),
            "heating": ("district_heat", 2, "2.2", "kWh"),
            "steam": ("district_heat", 2, "2.2", "kWh"),

            # Scope 3 - Various
            "waste": ("waste_mixed_landfill", 3, "3.5", "kg"),
            "flight": ("flight_medium_economy", 3, "3.6", "km"),
            "air travel": ("flight_medium_economy", 3, "3.6", "km"),
            "hotel": ("hotel_night", 3, "3.6", "nights"),
            "commute": ("commute_car_petrol", 3, "3.7", "km"),
            "spend": ("spend_other", 3, "3.1", "USD"),
            "purchase": ("spend_other", 3, "3.1", "USD"),
        }

        for header in headers:
            header_lower = header.lower().strip()

            # Check for date columns
            if any(d in header_lower for d in ["date", "period", "month", "year"]):
                date_column = header
                mappings.append(ColumnMapping(
                    original_header=header,
                    activity_key=None,
                    scope=None,
                    category_code=None,
                    detected_unit=None,
                    column_type="date",
                    confidence=0.9,
                ))
                continue

            # Check for description columns
            if any(d in header_lower for d in ["description", "note", "comment", "detail"]):
                description_column = header
                mappings.append(ColumnMapping(
                    original_header=header,
                    activity_key=None,
                    scope=None,
                    category_code=None,
                    detected_unit=None,
                    column_type="description",
                    confidence=0.9,
                ))
                continue

            # Check for quantity/unit columns
            if any(q in header_lower for q in ["quantity", "amount", "value", "usage"]):
                quantity_column = header
                mappings.append(ColumnMapping(
                    original_header=header,
                    activity_key=None,
                    scope=None,
                    category_code=None,
                    detected_unit=None,
                    column_type="quantity",
                    confidence=0.8,
                ))
                continue

            if header_lower == "unit" or header_lower == "units":
                unit_column = header
                mappings.append(ColumnMapping(
                    original_header=header,
                    activity_key=None,
                    scope=None,
                    category_code=None,
                    detected_unit=None,
                    column_type="unit",
                    confidence=0.9,
                ))
                continue

            # Try to match activity patterns
            matched = False
            for pattern, (activity_key, scope, category, unit) in ACTIVITY_PATTERNS.items():
                if pattern in header_lower:
                    # Try to detect unit from header
                    detected_unit = unit
                    if "kwh" in header_lower:
                        detected_unit = "kWh"
                    elif "mwh" in header_lower:
                        detected_unit = "MWh"
                    elif "m³" in header_lower or "m3" in header_lower or "cubic" in header_lower:
                        detected_unit = "m³"
                    elif "liter" in header_lower or "litre" in header_lower:
                        detected_unit = "liters"
                    elif "gallon" in header_lower:
                        detected_unit = "gallons"
                    elif "kg" in header_lower:
                        detected_unit = "kg"
                    elif "tonne" in header_lower or "ton" in header_lower:
                        detected_unit = "tonnes"
                    elif "km" in header_lower:
                        detected_unit = "km"
                    elif "mile" in header_lower:
                        detected_unit = "miles"

                    mappings.append(ColumnMapping(
                        original_header=header,
                        activity_key=activity_key,
                        scope=scope,
                        category_code=category,
                        detected_unit=detected_unit,
                        column_type="activity",
                        confidence=0.7,
                        notes="Matched by keyword pattern",
                    ))
                    matched = True
                    break

            if not matched:
                # Unknown column - ignore
                mappings.append(ColumnMapping(
                    original_header=header,
                    activity_key=None,
                    scope=None,
                    category_code=None,
                    detected_unit=None,
                    column_type="ignore",
                    confidence=0.5,
                    notes="Could not match to known activity type",
                ))
                warnings.append(f"Column '{header}' could not be mapped automatically")

        # Determine structure
        activity_count = sum(1 for m in mappings if m.column_type == "activity")
        if activity_count == 0:
            detected_structure = "single_activity"
            warnings.append("No activity columns detected - may need manual mapping")
        elif activity_count == 1:
            detected_structure = "single_activity"
        else:
            detected_structure = "multi_activity"

        return MappingResult(
            success=True,
            mappings=mappings,
            detected_structure=detected_structure,
            quantity_column=quantity_column,
            unit_column=unit_column,
            date_column=date_column,
            description_column=description_column,
            warnings=warnings,
            ai_notes="Rule-based mapping (AI not available)",
        )

    def suggest_activity_key(self, text: str) -> Optional[str]:
        """
        Suggest an activity_key for a text description.

        Uses AI if available, otherwise keyword matching.
        """
        if self.claude.is_available():
            prompt = f"""What activity_key best matches this description?
Description: "{text}"

Respond with just the activity_key string, nothing else.
If no match, respond with "null"."""

            response = self.claude.analyze(prompt, json_response=False, max_tokens=100)
            if response.success:
                result = response.content.strip().strip('"')
                return result if result != "null" else None

        # Fallback to keyword matching
        text_lower = text.lower()
        if "electric" in text_lower:
            return "electricity_global"
        if "gas" in text_lower:
            return "natural_gas_volume"
        if "diesel" in text_lower:
            return "diesel_volume"
        if "flight" in text_lower or "air" in text_lower:
            return "flight_medium_economy"
        if "waste" in text_lower:
            return "waste_mixed_landfill"

        return None
