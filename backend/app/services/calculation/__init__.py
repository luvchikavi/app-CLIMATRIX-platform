"""
Calculation Pipeline - 3-stage emission calculation engine.

Stage 1: Normalizer - Convert units to SI base using Pint
Stage 2: Resolver - Find emission factor with fallback strategies
Stage 3: Calculator - Apply appropriate calculation strategy

Usage:
    pipeline = CalculationPipeline(session)
    result = await pipeline.calculate(ActivityInput(...))
"""
from app.services.calculation.pipeline import CalculationPipeline, ActivityInput, CalculationError
from app.services.calculation.normalizer import UnitNormalizer
from app.services.calculation.resolver import FactorResolver
from app.services.calculation.result import CalculationResult

__all__ = ["CalculationPipeline", "ActivityInput", "CalculationError", "UnitNormalizer", "FactorResolver", "CalculationResult"]
