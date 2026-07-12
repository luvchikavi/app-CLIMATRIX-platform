"""Tests for the file loader (CSV path — deterministic, no API key)."""

import io

import pytest

from app.services.ingestion.loader import load, load_with_skipped, is_tabular, RawTable


def test_is_tabular():
    assert is_tabular("data.csv")
    assert is_tabular("Book1.xlsx")
    assert not is_tabular("invoice.pdf")
    assert not is_tabular("meter.jpg")


def test_llm_formats_raise():
    with pytest.raises(NotImplementedError):
        load(b"whatever", "utility_bill.pdf")


def test_csv_loads_into_rawtable():
    csv = (
        "Activity,Quantity,Unit\n"
        "Office electricity,45600,kWh\n"
        "Diesel generators,720000,liters\n"
        "Business flights,60000,km\n"
    ).encode()
    tables = load(csv, "footprint.csv")
    assert len(tables) == 1
    t = tables[0]
    assert isinstance(t, RawTable)
    assert t.columns == ["Activity", "Quantity", "Unit"]
    assert t.row_count == 3
    assert t.rows[0]["Activity"] == "Office electricity"
    assert t.rows[0]["Quantity"] == 45600
    assert t.rows[2]["Unit"] == "km"


def test_csv_blank_cells_become_none():
    csv = "Activity,Quantity,Unit\nElectricity,,kWh\n".encode()
    t = load(csv, "x.csv")[0]
    assert t.rows[0]["Quantity"] is None


def _two_sheet_xlsx() -> bytes:
    """Workbook with one real data sheet and one empty 'Instructions' sheet."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(["Activity", "Quantity", "Unit", "Site"])
    ws.append(["Electricity", 100, "kWh", "HQ"])
    ws.append(["Diesel", 50, "liters", "HQ"])
    ws.append(["Natural gas", 900, "kWh", "Plant"])
    wb.create_sheet("Instructions")  # empty — must be skipped, but visibly so
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_xlsx_skipped_sheets_are_reported():
    tables, skipped = load_with_skipped(_two_sheet_xlsx(), "book.xlsx")
    assert [t.sheet for t in tables] == ["Data"]
    assert skipped == ["Instructions"]


def test_load_contract_unchanged():
    # load() keeps its original list-of-RawTable contract for existing callers.
    tables = load(_two_sheet_xlsx(), "book.xlsx")
    assert isinstance(tables, list)
    assert [t.sheet for t in tables] == ["Data"]
