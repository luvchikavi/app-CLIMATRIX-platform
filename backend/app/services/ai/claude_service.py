"""
Claude Service - Core wrapper for Anthropic Claude API.

Provides structured methods for AI-powered emission data processing:
- Column mapping for file imports
- Data extraction from unstructured text
- Validation and error correction suggestions
"""
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from anthropic import Anthropic, APIError, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ClaudeResponse:
    """Structured response from Claude API."""
    success: bool
    content: str | dict | list
    model: str
    usage: dict
    error: Optional[str] = None


class ClaudeService:
    """
    Core service for Claude API interactions.

    Handles:
    - API initialization and configuration
    - Structured prompting with system context
    - JSON response parsing
    - Error handling and retries
    - Token usage tracking

    Usage:
        service = ClaudeService()
        response = await service.analyze(
            prompt="Map these columns to emission factors",
            context={"columns": ["Gas Usage", "Electricity kWh"]}
        )
    """

    # System prompt with emission factor context
    SYSTEM_PROMPT = """You are an expert GHG emissions data analyst assistant integrated into CLIMATRIX,
a carbon accounting platform. Your role is to help process, validate, and map emission data.

You have deep knowledge of:
- GHG Protocol scopes (1, 2, 3) and categories
- Common emission factors and their sources (DEFRA, EPA, IEA, IPCC)
- Unit conversions for energy, fuel, distance, mass
- Industry-standard activity classifications

When processing data:
1. Be precise with units and quantities
2. Map to the most specific activity_key available
3. Flag any data quality issues or anomalies
4. Provide confidence scores for mappings
5. Always respond in valid JSON format when requested

Available activity_keys for mapping include:
- Scope 1.1 (Stationary): natural_gas_volume, natural_gas_energy, diesel_volume, lpg_volume, coal_mass
- Scope 1.2 (Mobile): petrol_vehicle_km, diesel_vehicle_km, petrol_vehicle_liters, diesel_vehicle_liters
- Scope 1.3 (Fugitive): refrigerant_r134a, refrigerant_r410a, refrigerant_r32, refrigerant_r404a, sf6_leakage
- Scope 2: electricity_il, electricity_uk, electricity_us, electricity_de, electricity_global, district_heat
- Scope 3.1 (Purchases): spend_* categories (office_supplies, it_equipment, professional_services, etc.)
- Scope 3.5 (Waste): waste_*_landfill, waste_*_recycled, waste_*_incinerated
- Scope 3.6 (Travel): flight_short_economy, flight_medium_economy, flight_long_economy, hotel_night
- Scope 3.7 (Commuting): commute_car_petrol, commute_car_diesel, commute_bus, commute_rail"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Claude service.

        Args:
            api_key: Anthropic API key (defaults to settings.anthropic_api_key)
            model: Claude model to use (defaults to settings.claude_model)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model
        self._client: Optional[Anthropic] = None

    @property
    def client(self) -> Anthropic:
        """Lazy-load Anthropic client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Anthropic API key not configured. "
                    "Set ANTHROPIC_API_KEY in your .env file."
                )
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if Claude service is available (API key configured)."""
        return bool(self.api_key) and settings.ai_extraction_enabled

    def analyze(
        self,
        prompt: str,
        context: Optional[dict] = None,
        json_response: bool = True,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> ClaudeResponse:
        """
        Send analysis request to Claude.

        Args:
            prompt: The analysis prompt
            context: Additional context data to include
            json_response: Whether to request JSON formatted response
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0 = deterministic)

        Returns:
            ClaudeResponse with parsed content
        """
        if not self.is_available():
            return ClaudeResponse(
                success=False,
                content={},
                model=self.model,
                usage={},
                error="AI service not available. Configure ANTHROPIC_API_KEY.",
            )

        # Build the full prompt
        full_prompt = prompt
        if context:
            full_prompt += f"\n\nContext data:\n```json\n{json.dumps(context, indent=2)}\n```"

        if json_response:
            full_prompt += "\n\nRespond with valid JSON only. No markdown code blocks or explanation."

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
            )

            content = response.content[0].text

            # Parse JSON if requested
            if json_response:
                try:
                    # Handle case where Claude wraps in markdown
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]
                    content = json.loads(content.strip())
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    # Return raw content if JSON parsing fails
                    pass

            return ClaudeResponse(
                success=True,
                content=content,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            )

        except RateLimitError as e:
            logger.error(f"Claude rate limit exceeded: {e}")
            return ClaudeResponse(
                success=False,
                content={},
                model=self.model,
                usage={},
                error="Rate limit exceeded. Please try again later.",
            )

        except APIError as e:
            logger.error(f"Claude API error: {e}")
            return ClaudeResponse(
                success=False,
                content={},
                model=self.model,
                usage={},
                error=f"API error: {str(e)}",
            )

        except Exception as e:
            logger.error(f"Unexpected error calling Claude: {e}")
            return ClaudeResponse(
                success=False,
                content={},
                model=self.model,
                usage={},
                error=f"Unexpected error: {str(e)}",
            )

    def analyze_batch(
        self,
        items: list[dict],
        prompt_template: str,
        max_tokens: int = 4096,
    ) -> list[ClaudeResponse]:
        """
        Analyze multiple items with a template prompt.

        Args:
            items: List of items to analyze
            prompt_template: Template with {item} placeholder
            max_tokens: Maximum tokens per response

        Returns:
            List of ClaudeResponse objects
        """
        results = []
        for item in items:
            prompt = prompt_template.format(item=json.dumps(item))
            response = self.analyze(prompt, max_tokens=max_tokens)
            results.append(response)
        return results
