"""Tests for the template fast-path and the ParsingContext injection."""

import io

import openpyxl
import pytest

from app.services.ingestion.context import ParsingContext, build_parsing_context
from app.services.ingestion.template_bridge import detect_template, map_template


def _workbook(sheet_specs: dict[str, list[list]]) -> bytes:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheet_specs.items():
        ws = wb.create_sheet(title=name)
        for row in rows:
            ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _template_sheet(header: list[str], data: list[list]) -> list[list]:
    # Mirrors the real template layout: banner, blurb, legend, blank, header, data.
    pad = [""] * (len(header) - 1)
    return [
        ["Title"] + pad,
        ["Blurb"] + pad,
        ["Legend"] + pad,
        [""] * len(header),
        header,
        *data,
    ]


STATIONARY_HEADER = [
    "Site",
    "Description",
    "Fuel_Type",
    "Year",
    "Calc_Type",
    "Physical_Amount",
    "Physical_Unit",
    "Spend_Amount",
    "Spend_Currency",
    "Comment",
]


def test_detect_template_requires_known_sheets():
    template = _workbook(
        {
            "Scope1_Stationary": _template_sheet(
                STATIONARY_HEADER,
                [
                    [
                        "",
                        "Boiler",
                        "Natural Gas",
                        2024,
                        "Physical",
                        100,
                        "kWh",
                        "",
                        "",
                        "",
                    ]
                ],
            ),
            "Cat5_Waste": [["x"]],
        }
    )
    assert detect_template(template, "client.xlsx") is True

    foreign = _workbook({"Sheet1": [["Item", "Amount"], ["Diesel", 10]]})
    assert detect_template(foreign, "client.xlsx") is False
    assert detect_template(b"not a workbook", "client.xlsx") is False
    assert detect_template(template, "client.csv") is False


def test_map_template_stages_real_rows_and_skips_scaffold():
    content = _workbook(
        {
            "Scope1_Stationary": _template_sheet(
                STATIONARY_HEADER,
                [
                    # real physical row
                    [
                        "",
                        "Boiler",
                        "Natural Gas",
                        2024,
                        "Physical",
                        500,
                        "kWh",
                        "",
                        "",
                        "",
                    ],
                    # scaffold row — description but no amounts → must not stage
                    [
                        "",
                        "Diesel Generator",
                        "Diesel",
                        "",
                        "Physical",
                        "",
                        "",
                        "",
                        "",
                        "",
                    ],
                ],
            ),
            "Scope2_Electricity": [["only-header-noise"]],
        }
    )
    result = map_template(content, "client.xlsx")
    assert result is not None
    tables = {tbl.sheet: rows for tbl, rows in result}
    assert "Scope1_Stationary" in tables
    rows = tables["Scope1_Stationary"]
    assert len(rows) == 1
    row = rows[0]
    assert row.quantity == 500
    assert row.unit == "kWh"
    assert row.scope == 1
    assert row.category_code == "1.1"
    assert row.activity_key  # grounded in the real catalog key space
    assert row.llm_confidence == 1.0


def test_map_template_returns_none_for_foreign_file():
    foreign = _workbook({"Data": [["Item", "Qty"], ["Diesel", 10]]})
    assert map_template(foreign, "client.xlsx") is None


def test_parsing_context_prompt_block_renders_profile():
    ctx = ParsingContext(
        org_name="SHN Industries",
        industry="manufacturing",
        country_code="IL",
        default_region="IL",
        currency="ILS",
        unit_system="metric",
        period_year=2024,
        sites=[{"name": "Tel Aviv HQ", "country_code": "IL"}],
        relevant={"1.2": {"name": "Mobile Combustion", "expected_form": "invoices"}},
        excluded={"2.3": "No district heating"},
    )
    block = ctx.prompt_block()
    assert "SHN Industries" in block
    assert "ILS" in block
    assert "Tel Aviv HQ" in block
    assert "1.2 Mobile Combustion [expect invoices]" in block
    assert "2.3 (No district heating)" in block
    assert "reporting year: 2024" in block


@pytest.mark.asyncio
async def test_build_parsing_context_reads_org_and_profile(
    client, auth_headers, test_session, test_org, test_period
):
    await client.patch(
        "/api/organization",
        json={"currency": "ILS", "unit_system": "metric"},
        headers=auth_headers,
    )
    await client.put(
        "/api/hub/profile",
        json={
            "entries": [
                {
                    "category_code": "1.1",
                    "relevance": "relevant",
                    "expected_form": "invoices",
                },
                {
                    "category_code": "3.14",
                    "relevance": "not_relevant",
                    "exclusion_reason": "No franchises",
                },
            ]
        },
        headers=auth_headers,
    )
    ctx = await build_parsing_context(test_session, test_org.id, test_period.id)
    assert ctx.currency == "ILS"
    assert ctx.period_year == 2025
    assert "1.1" in ctx.relevant
    assert ctx.relevant["1.1"]["expected_form"] == "invoices"
    assert ctx.excluded["3.14"] == "No franchises"
