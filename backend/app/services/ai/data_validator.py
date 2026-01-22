"""
Data Validator - AI-assisted validation and correction of emission data.

Validates:
- Quantity reasonableness (flags suspicious values)
- Unit consistency (detects mismatched units)
- Activity type appropriateness
- Data completeness

Suggests corrections for common errors.
"""
import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.services.ai.claude_service import ClaudeService


@dataclass
class ValidationIssue:
    """Single validation issue found."""
    field: str  # "quantity", "unit", "activity_key", etc.
    severity: str  # "error", "warning", "info"
    message: str
    original_value: str
    suggested_value: Optional[str] = None
    confidence: float = 0.0


@dataclass
class ValidationResult:
    """Complete validation result for an activity."""
    is_valid: bool
    issues: list[ValidationIssue]
    corrected_data: Optional[dict] = None  # Suggested corrections
    ai_notes: Optional[str] = None


@dataclass
class BatchValidationResult:
    """Validation result for a batch of activities."""
    total_records: int
    valid_count: int
    warning_count: int
    error_count: int
    results: list[ValidationResult]
    summary: str


class DataValidator:
    """
    Validates emission data and suggests corrections.

    Validation Rules:
    1. Quantity bounds: Values should be within reasonable ranges
    2. Unit consistency: Units should match activity type
    3. Missing data: Required fields should be present
    4. Anomaly detection: Flag unusual values

    Usage:
        validator = DataValidator()
        result = validator.validate_activity({
            "activity_key": "natural_gas_volume",
            "quantity": 1000000,  # Suspiciously high
            "unit": "m³"
        })
    """

    # Typical ranges for different activities (per month/year basis)
    QUANTITY_BOUNDS = {
        # Scope 1.1 - Stationary (monthly ranges for typical office building)
        "natural_gas_volume": (10, 100000, "m³"),  # min, max, unit
        "natural_gas_energy": (100, 1000000, "kWh"),
        "diesel_volume": (10, 50000, "liters"),
        "lpg_volume": (5, 10000, "liters"),
        "coal_mass": (100, 100000, "kg"),

        # Scope 1.2 - Mobile (per vehicle per month)
        "petrol_vehicle_km": (100, 10000, "km"),
        "diesel_vehicle_km": (100, 15000, "km"),
        "petrol_vehicle_liters": (20, 2000, "liters"),
        "diesel_vehicle_liters": (30, 3000, "liters"),

        # Scope 1.3 - Fugitive (annual)
        "refrigerant_r134a": (0.1, 1000, "kg"),
        "refrigerant_r410a": (0.1, 1000, "kg"),
        "refrigerant_r32": (0.1, 1000, "kg"),
        "sf6_leakage": (0.001, 100, "kg"),

        # Scope 2 - Electricity (monthly for office)
        "electricity_global": (100, 1000000, "kWh"),
        "electricity_il": (100, 1000000, "kWh"),
        "electricity_uk": (100, 1000000, "kWh"),
        "electricity_us": (100, 1000000, "kWh"),
        "district_heat": (100, 500000, "kWh"),

        # Scope 3.1 - Purchases (monthly spend)
        "spend_office_supplies": (100, 100000, "USD"),
        "spend_it_equipment": (1000, 1000000, "USD"),
        "spend_professional_services": (1000, 500000, "USD"),
        "spend_other": (100, 1000000, "USD"),

        # Scope 3.5 - Waste (monthly)
        "waste_mixed_landfill": (10, 100000, "kg"),
        "waste_paper_recycled": (5, 50000, "kg"),
        "waste_plastic_recycled": (1, 10000, "kg"),

        # Scope 3.6 - Travel
        "flight_short_economy": (100, 5000, "km"),
        "flight_medium_economy": (500, 10000, "km"),
        "flight_long_economy": (3000, 20000, "km"),
        "hotel_night": (1, 100, "nights"),

        # Scope 3.7 - Commuting (per employee per month)
        "commute_car_petrol": (100, 5000, "km"),
        "commute_car_diesel": (100, 5000, "km"),
        "commute_bus": (100, 3000, "km"),
        "commute_rail": (100, 3000, "km"),
    }

    VALIDATION_PROMPT = """Validate this emission activity data for reasonableness.

Activity data:
{data}

Check for:
1. Is the quantity reasonable for this activity type?
2. Is the unit correct for this activity?
3. Are there any data quality issues?
4. Should any corrections be suggested?

Consider industry context - this could be from:
- Small office (10-50 employees)
- Medium business (50-500 employees)
- Large corporation (500+ employees)
- Manufacturing facility
- Retail location

Respond with JSON:
{{
    "is_valid": true/false,
    "issues": [
        {{
            "field": "quantity" | "unit" | "activity_key" | "description",
            "severity": "error" | "warning" | "info",
            "message": "explanation",
            "original_value": "the value being flagged",
            "suggested_value": "suggested correction if applicable",
            "confidence": 0.0-1.0
        }}
    ],
    "corrected_data": {{
        "activity_key": "...",
        "quantity": ...,
        "unit": "..."
    }},
    "notes": "any helpful context"
}}"""

    def __init__(self, claude_service: Optional[ClaudeService] = None):
        """Initialize with Claude service."""
        self.claude = claude_service or ClaudeService()

    def validate_activity(self, activity_data: dict) -> ValidationResult:
        """
        Validate a single activity.

        Args:
            activity_data: Dictionary with activity_key, quantity, unit, etc.

        Returns:
            ValidationResult with issues and suggestions
        """
        # Try AI validation first
        if self.claude.is_available():
            return self._ai_validate(activity_data)

        # Fall back to rule-based validation
        return self._rule_validate(activity_data)

    def _ai_validate(self, activity_data: dict) -> ValidationResult:
        """Use Claude AI to validate data."""
        prompt = self.VALIDATION_PROMPT.format(
            data=json.dumps(activity_data, indent=2, default=str)
        )
        response = self.claude.analyze(prompt, json_response=True)

        if not response.success:
            return self._rule_validate(activity_data)

        try:
            data = response.content
            issues = [
                ValidationIssue(
                    field=i["field"],
                    severity=i["severity"],
                    message=i["message"],
                    original_value=str(i.get("original_value", "")),
                    suggested_value=i.get("suggested_value"),
                    confidence=i.get("confidence", 0.8),
                )
                for i in data.get("issues", [])
            ]

            return ValidationResult(
                is_valid=data.get("is_valid", True),
                issues=issues,
                corrected_data=data.get("corrected_data"),
                ai_notes=data.get("notes"),
            )

        except (KeyError, TypeError) as e:
            return self._rule_validate(activity_data)

    def _rule_validate(self, activity_data: dict) -> ValidationResult:
        """
        Rule-based validation fallback.

        Checks quantity bounds and unit consistency.
        """
        issues = []
        activity_key = activity_data.get("activity_key", "")
        quantity = activity_data.get("quantity")
        unit = activity_data.get("unit", "")

        # Check required fields
        if not activity_key:
            issues.append(ValidationIssue(
                field="activity_key",
                severity="error",
                message="Activity key is required",
                original_value="",
            ))

        if quantity is None:
            issues.append(ValidationIssue(
                field="quantity",
                severity="error",
                message="Quantity is required",
                original_value="",
            ))

        if not unit:
            issues.append(ValidationIssue(
                field="unit",
                severity="error",
                message="Unit is required",
                original_value="",
            ))

        # Check quantity bounds
        if activity_key in self.QUANTITY_BOUNDS and quantity is not None:
            min_val, max_val, expected_unit = self.QUANTITY_BOUNDS[activity_key]

            try:
                qty = float(quantity)

                if qty <= 0:
                    issues.append(ValidationIssue(
                        field="quantity",
                        severity="error",
                        message="Quantity must be positive",
                        original_value=str(quantity),
                        suggested_value=str(abs(qty)),
                        confidence=0.9,
                    ))

                elif qty < min_val * 0.1:  # 10% of minimum
                    issues.append(ValidationIssue(
                        field="quantity",
                        severity="warning",
                        message=f"Quantity seems unusually low for {activity_key}. "
                                f"Typical range: {min_val} - {max_val} {expected_unit}",
                        original_value=str(quantity),
                        confidence=0.7,
                    ))

                elif qty > max_val * 10:  # 10x maximum
                    issues.append(ValidationIssue(
                        field="quantity",
                        severity="warning",
                        message=f"Quantity seems unusually high for {activity_key}. "
                                f"Typical range: {min_val} - {max_val} {expected_unit}. "
                                f"Check if units are correct.",
                        original_value=str(quantity),
                        confidence=0.7,
                    ))

            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    field="quantity",
                    severity="error",
                    message="Quantity must be a valid number",
                    original_value=str(quantity),
                ))

            # Check unit consistency
            if unit and expected_unit:
                unit_lower = unit.lower().strip()
                expected_lower = expected_unit.lower()

                # Common unit mismatches
                unit_aliases = {
                    "kwh": ["kwh", "kw/h", "kw"],
                    "mwh": ["mwh", "mw/h"],
                    "m³": ["m³", "m3", "cubic meters", "cubic metres", "cbm"],
                    "liters": ["liters", "litres", "l", "ltr"],
                    "gallons": ["gallons", "gal"],
                    "kg": ["kg", "kilograms", "kgs"],
                    "tonnes": ["tonnes", "tons", "t", "metric tons"],
                    "km": ["km", "kilometers", "kilometres"],
                    "miles": ["miles", "mi"],
                    "usd": ["usd", "$", "dollars"],
                }

                expected_aliases = unit_aliases.get(expected_lower, [expected_lower])

                if unit_lower not in expected_aliases:
                    issues.append(ValidationIssue(
                        field="unit",
                        severity="warning",
                        message=f"Unit '{unit}' may not match expected unit '{expected_unit}' "
                                f"for activity '{activity_key}'",
                        original_value=unit,
                        suggested_value=expected_unit,
                        confidence=0.6,
                    ))

        # Determine overall validity
        has_errors = any(i.severity == "error" for i in issues)

        return ValidationResult(
            is_valid=not has_errors,
            issues=issues,
            corrected_data=None,
            ai_notes="Rule-based validation (AI not available)",
        )

    def validate_batch(self, activities: list[dict]) -> BatchValidationResult:
        """
        Validate a batch of activities.

        Args:
            activities: List of activity dictionaries

        Returns:
            BatchValidationResult with summary statistics
        """
        results = []
        valid_count = 0
        warning_count = 0
        error_count = 0

        for activity in activities:
            result = self.validate_activity(activity)
            results.append(result)

            if result.is_valid:
                if any(i.severity == "warning" for i in result.issues):
                    warning_count += 1
                else:
                    valid_count += 1
            else:
                error_count += 1

        total = len(activities)
        summary = (
            f"Validated {total} records: "
            f"{valid_count} valid, {warning_count} warnings, {error_count} errors"
        )

        return BatchValidationResult(
            total_records=total,
            valid_count=valid_count,
            warning_count=warning_count,
            error_count=error_count,
            results=results,
            summary=summary,
        )
