"""
Template Parser Service

Parses the CLIMATRIX GHG Data Collection Template (multi-sheet Excel)
and converts it to standardized activity records for import.
"""

from .parser import TemplateParser
from .models import ParsedActivity, ParseResult, SheetResult

__all__ = ['TemplateParser', 'ParsedActivity', 'ParseResult', 'SheetResult']
