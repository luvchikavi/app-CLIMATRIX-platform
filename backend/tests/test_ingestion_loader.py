"""Tests for the file loader (CSV path — deterministic, no API key)."""
import pytest

from app.services.ingestion.loader import load, is_tabular, RawTable


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
