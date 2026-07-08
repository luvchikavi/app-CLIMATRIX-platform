"""ParsingContext — everything the org already told us, injected into every parse.

The Data Hub collects a standing profile (Layer 0: country/currency/units/industry;
Layer 1: which GHG categories are relevant and what backs them). This module turns
that profile into a compact context block the LLM mapper reads BEFORE it sees a
single row — so the parser stops asking what the organization already answered,
and its guesses are anchored to who the client actually is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Organization, ReportingPeriod, Site
from app.models.hub import CATEGORY_BY_CODE, CategoryProfile, CategoryRelevance


@dataclass
class ParsingContext:
    """The org's standing answers, ready to prepend to mapper prompts."""

    org_name: str = ""
    industry: str | None = None
    country_code: str | None = None
    default_region: str = "Global"
    currency: str | None = None
    unit_system: str = "metric"
    period_name: str | None = None
    period_year: int | None = None
    sites: list[dict] = field(default_factory=list)  # {name, country_code}
    # category_code -> {name, expected_form, data_owner}
    relevant: dict[str, dict] = field(default_factory=dict)
    # category_code -> exclusion reason
    excluded: dict[str, str] = field(default_factory=dict)

    def prompt_block(self) -> str:
        """A compact, injection-safe context block for LLM system prompts."""
        lines = ["ORGANIZATION CONTEXT (declared by the client — trust it):"]
        head = []
        if self.org_name:
            head.append(self.org_name)
        if self.industry:
            head.append(f"industry: {self.industry}")
        if self.country_code:
            head.append(f"country: {self.country_code}")
        if head:
            lines.append("- " + " | ".join(head))
        lines.append(
            f"- Emission-factor region: {self.default_region}"
            + (f" | reporting year: {self.period_year}" if self.period_year else "")
        )
        if self.currency:
            lines.append(
                f"- Currency: {self.currency} — bare money amounts are {self.currency} "
                "unless the sheet clearly says otherwise."
            )
        lines.append(
            f"- Unit system: {self.unit_system} — read ambiguous units "
            f"({'gal/ton are US units' if self.unit_system == 'imperial' else 'ton = metric tonne, gal unlikely'}) accordingly."
        )
        if self.sites:
            site_bits = ", ".join(
                f"{s['name']}"
                + (f" ({s['country_code']})" if s.get("country_code") else "")
                for s in self.sites[:8]
            )
            lines.append(f"- Sites: {site_bits}")
        if self.relevant:
            cats = "; ".join(
                f"{code} {info['name']}"
                + (
                    f" [expect {info['expected_form']}]"
                    if info.get("expected_form")
                    else ""
                )
                for code, info in sorted(self.relevant.items())
            )
            lines.append(f"- EXPECTED categories (client will report these): {cats}")
        if self.excluded:
            cats = "; ".join(
                f"{code} ({reason})" for code, reason in sorted(self.excluded.items())
            )
            lines.append(
                f"- EXCLUDED categories (client declared not relevant): {cats} — "
                "data matching these is unexpected; map it but flag it."
            )
        return "\n".join(lines)


async def build_parsing_context(
    session: AsyncSession,
    organization_id: UUID,
    reporting_period_id: UUID | None = None,
) -> ParsingContext:
    """Assemble the context from Organization + Sites + ReportingPeriod + hub profile."""
    ctx = ParsingContext()

    org = await session.get(Organization, organization_id)
    if org:
        ctx.org_name = org.name
        ctx.industry = org.industry_code
        ctx.country_code = org.country_code
        ctx.default_region = org.default_region or "Global"
        ctx.currency = org.currency
        ctx.unit_system = org.unit_system or "metric"

    if reporting_period_id:
        period = await session.get(ReportingPeriod, reporting_period_id)
        if period and period.organization_id == organization_id:
            ctx.period_name = period.name
            if period.start_date:
                ctx.period_year = period.start_date.year

    sites = (
        (
            await session.execute(
                select(Site).where(
                    Site.organization_id == organization_id,
                    Site.is_active == True,  # noqa: E712
                )
            )
        )
        .scalars()
        .all()
    )
    ctx.sites = [{"name": s.name, "country_code": s.country_code} for s in sites]

    # Org-level hub profile (site-level overrides are a review-time concern, not
    # a parse-time one — the org layer is the right prior for mapping).
    profiles = (
        (
            await session.execute(
                select(CategoryProfile).where(
                    CategoryProfile.organization_id == organization_id,
                    CategoryProfile.site_id.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    for p in profiles:
        relevance = p.relevance if isinstance(p.relevance, str) else p.relevance.value
        cat = CATEGORY_BY_CODE.get(p.category_code, {})
        if relevance == CategoryRelevance.RELEVANT.value:
            form = (
                p.expected_form
                if isinstance(p.expected_form, str)
                else (p.expected_form.value if p.expected_form else None)
            )
            ctx.relevant[p.category_code] = {
                "name": cat.get("name", p.category_code),
                "expected_form": form,
                "data_owner": p.data_owner,
            }
        elif relevance == CategoryRelevance.NOT_RELEVANT.value:
            ctx.excluded[p.category_code] = p.exclusion_reason or "excluded"

    return ctx
