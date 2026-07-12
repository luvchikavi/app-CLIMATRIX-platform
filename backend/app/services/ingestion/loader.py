"""File loader — turn any uploaded file into normalized ``RawTable`` objects the
mapper can reason over, format-agnostic.

CSV / XLSX reuse the existing FileAnalyzer for header + multi-sheet detection,
then re-read the full rows. PDF / image / email go through the LLM vision path,
which is built together with the mapper (raises NotImplementedError until then).
The tabular path is deterministic — testable without an API key.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from app.services.ai.file_analyzer import FileAnalyzer, FileType

_LLM_FORMATS = (
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".eml",
    ".txt",
    ".msg",
)


@dataclass
class RawTable:
    """A single normalized table extracted from an uploaded file."""

    source: str  # filename
    sheet: str  # sheet name ("" for CSV)
    columns: list[str]
    rows: list[dict]  # full rows as {column: value}, NaN -> None
    detected_scope: int | None = None
    detected_category: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def preview(self, n: int = 20) -> list[dict]:
        return self.rows[:n]


def is_tabular(filename: str) -> bool:
    return not filename.lower().endswith(_LLM_FORMATS)


def load(content: bytes, filename: str) -> list[RawTable]:
    """Load a tabular file (CSV/XLSX) into RawTable[].

    Raises NotImplementedError for formats that need the LLM/vision path
    (PDF/image/email) — those are handled by the mapper once wired.
    """
    if not is_tabular(filename):
        raise NotImplementedError(
            f"{filename}: PDF/image/email extraction uses the LLM vision path "
            f"(built with the mapper)."
        )

    analysis = FileAnalyzer().analyze(content, filename)
    tables: list[RawTable] = []
    for sheet in analysis.sheets:
        if sheet.is_empty or sheet.is_metadata_only:
            continue
        rows = _read_full_rows(
            content, analysis.file_type, sheet.sheet_name, sheet.header_row
        )
        tables.append(
            RawTable(
                source=filename,
                sheet=sheet.sheet_name or "",
                columns=[str(c) for c in sheet.columns],
                rows=rows,
                detected_scope=sheet.detected_scope,
                detected_category=sheet.detected_category,
                warnings=list(analysis.warnings),
            )
        )
    return tables


def _read_full_rows(
    content: bytes, file_type, sheet_name: str, header_row: int
) -> list[dict]:
    import pandas as pd

    if file_type == FileType.CSV:
        df = pd.read_csv(io.BytesIO(content), header=header_row)
    else:
        df = pd.read_excel(
            io.BytesIO(content), sheet_name=sheet_name, header=header_row
        )
    # NaN -> None so downstream JSON/LLM sees explicit nulls, not floats
    df = df.astype(object).where(df.notna(), None)
    return df.to_dict(orient="records")
