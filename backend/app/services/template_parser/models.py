"""
Data models for template parser.
"""
from dataclasses import dataclass, field
from typing import Optional
from decimal import Decimal


@dataclass
class ParsedActivity:
    """A single parsed activity ready for import."""
    scope: int
    category_code: str
    activity_key: str
    description: str
    quantity: Decimal
    unit: str
    
    # Optional fields
    activity_date: Optional[str] = None
    site: Optional[str] = None
    
    # Source tracking
    source_sheet: str = ""
    source_row: int = 0
    
    # Warnings/notes
    warnings: list[str] = field(default_factory=list)
    
    # Original data for debugging
    raw_data: dict = field(default_factory=dict)


@dataclass
class SheetResult:
    """Result of parsing a single sheet."""
    sheet_name: str
    scope: int
    category_code: str
    total_rows: int
    parsed_rows: int
    skipped_rows: int
    activities: list[ParsedActivity]
    errors: list[dict]
    warnings: list[str]


@dataclass  
class ParseResult:
    """Complete result of parsing a template file."""
    success: bool
    filename: str
    total_sheets: int
    processed_sheets: int
    total_activities: int
    
    # Results by sheet
    sheets: list[SheetResult]
    
    # All activities (flattened)
    activities: list[ParsedActivity]
    
    # Summary
    by_scope: dict = field(default_factory=dict)
    by_category: dict = field(default_factory=dict)
    
    # Errors
    errors: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
