"""Pure-function tests for the mapper's row filters (no LLM, no DB).

These guard the CLIMATRIX-template handling: skip the greyed SAMPLE row, drop
empty/scaffolding rows, and keep real data.
"""

from app.services.ingestion.mapper import (
    _is_empty_row,
    _is_placeholder,
    _is_sample_row,
)


def test_sample_row_detected():
    assert _is_sample_row({"desc": "Office heating - SAMPLE"}) is True
    assert _is_sample_row({"desc": "Monthly bill (SAMPLE)"}) is True


def test_sample_false_positive_guard():
    assert _is_sample_row({"desc": "Sample testing lab electricity"}) is False
    assert _is_sample_row({"desc": "Backup generator", "qty": 8000}) is False


def test_empty_row_all_blank():
    assert _is_empty_row({"a": None, "b": None, "c": "  "}) is True


def test_empty_row_only_unnamed_scaffolding():
    # A row whose only value sits in a pandas 'Unnamed:' helper column is template
    # noise ('Free text', 'Drop Down'), not data.
    assert (
        _is_empty_row({"Type": None, "Quantity": None, "Unnamed: 9": "Free text "})
        is True
    )


def test_real_row_is_not_empty():
    row = {"Type": "Diesel", "Quantity": 8000, "Unit": "liters"}
    assert _is_empty_row(row) is False
    assert _is_placeholder(row) is False
    assert _is_sample_row(row) is False


def test_placeholder_row():
    assert _is_placeholder({"a": "[Dropdown]", "b": "[Number]"}) is True
