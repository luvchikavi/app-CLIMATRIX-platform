"""File-upload security guard for the ingestion funnel.

The parser accepts "any file from any client", which makes the upload boundary a
real attack surface. This guard runs BEFORE a byte reaches the loader or the LLM:

  * size cap            — reject oversized uploads (DoS / memory) early
  * magic-byte sniffing — trust the actual bytes, not the filename extension, so a
                          disguised ``payload.exe`` renamed to ``data.xlsx`` is caught
  * extension allow-list— only tabular / document types we actually parse
  * cell sanitisation   — neutralise spreadsheet formula-injection (``=``/``+``/``-``/``@``
                          leading cells that Excel would execute on open)
  * prompt-injection    — strip/flag instruction-like text before it reaches the LLM
                          mapper, so uploaded data can't hijack the model

It never mutates the emissions ledger; it only decides whether bytes are safe to
parse and scrubs hostile text. Deterministic and unit-testable (no API key).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Accepted extensions (tabular now; PDF/image are wired with the vision path).
_ALLOWED_EXT = (
    ".csv",
    ".tsv",
    ".xlsx",
    ".xls",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
)

# Magic-byte signatures keyed by a human label. XLSX is a ZIP; XLS is an OLE2
# compound file; CSV/TSV/TXT are text and have no signature (validated as UTF-ish).
_SIGNATURES: list[tuple[str, bytes]] = [
    ("xlsx/zip", b"PK\x03\x04"),
    ("xls/ole2", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
    ("pdf", b"%PDF-"),
    ("png", b"\x89PNG\r\n\x1a\n"),
    ("jpg", b"\xff\xd8\xff"),
]

# Byte signatures that must NEVER be accepted regardless of filename.
_FORBIDDEN: list[tuple[str, bytes]] = [
    ("elf", b"\x7fELF"),
    ("mach-o", b"\xcf\xfa\xed\xfe"),
    ("mach-o", b"\xce\xfa\xed\xfe"),
    ("pe/exe", b"MZ"),
    ("shebang", b"#!"),
]

# Leading characters Excel/Sheets treat as the start of a formula.
_FORMULA_LEAD = ("=", "+", "-", "@", "\t=", "\r=", "\x09", "\x0d")

# Instruction-like phrases that shouldn't appear in *data* — likely prompt injection.
_INJECTION_PATTERNS = [
    re.compile(
        r"\bignore (all |the |your )?(previous|prior|above) instructions?\b", re.I
    ),
    re.compile(r"\bdisregard (all |the )?(previous|prior|system)\b", re.I),
    re.compile(r"\byou are now\b", re.I),
    re.compile(r"\bsystem prompt\b", re.I),
    re.compile(r"\bnew instructions?:\b", re.I),
    re.compile(
        r"\b(reveal|print|show) (your |the )?(system )?(prompt|instructions)\b", re.I
    ),
    re.compile(r"</?(system|assistant|user)>", re.I),
    re.compile(r"\[/?INST\]", re.I),
    re.compile(r"\boverride (all |your |all your )?(rules|instructions)\b", re.I),
    re.compile(r"\bact as (the )?(system|admin)\b", re.I),
    re.compile(r"\bdo anything now\b", re.I),
    re.compile(r"\bDAN\b"),  # case-sensitive on purpose — "Dan" is a name
    re.compile(r"```\s*(system|assistant|user)\b", re.I),  # markdown-fenced role block
    # Long base64-looking blob — data smuggling / encoded payloads are suspicious
    # in what should be tabular business data. Flagged, never blocked.
    re.compile(r"[A-Za-z0-9+/=]{80,}"),
]

# Zero-width / invisible characters used to split trigger words past naive scanners
# (e.g. "ig<ZWSP>nore previous instructions"). Stripped before pattern matching.
# U+200B ZWSP, U+200C ZWNJ, U+200D ZWJ, U+FEFF BOM/ZWNBSP.
_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"))

DEFAULT_MAX_BYTES = 50 * 1024 * 1024  # keep in step with settings.max_upload_size_mb


class FileRejected(Exception):
    """Raised when an upload is unsafe or unsupported. Carries a client-safe message."""

    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.message = message
        self.reason = reason  # machine code: too_large | forbidden_type | unsupported_type | type_mismatch | empty


@dataclass
class GuardReport:
    """Outcome of a passing check — the upload is safe to parse."""

    filename: str
    detected: str  # magic-byte label, or "text" for CSV/TSV/TXT
    size_bytes: int
    formula_cells_sanitised: int = 0
    injection_hits: int = 0
    warnings: list[str] = field(default_factory=list)


def _ext(filename: str) -> str:
    name = (filename or "").lower().strip()
    dot = name.rfind(".")
    return name[dot:] if dot != -1 else ""


def check_upload(
    content: bytes,
    filename: str,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> GuardReport:
    """Validate an uploaded file by SIZE, EXTENSION and MAGIC BYTES.

    Returns a :class:`GuardReport` when safe; raises :class:`FileRejected` otherwise.
    Bytes are trusted over the filename: a mismatch between declared extension and
    detected signature is rejected.
    """
    if not content:
        raise FileRejected("The file is empty.", "empty")
    if len(content) > max_bytes:
        mb = max_bytes // (1024 * 1024)
        raise FileRejected(f"File too large. Maximum size is {mb} MB.", "too_large")

    # 1) Never accept executables, whatever the name claims.
    head = content[:16]
    for label, sig in _FORBIDDEN:
        if head.startswith(sig):
            raise FileRejected(
                "This file looks like a program, not data. Upload a CSV, Excel, or PDF.",
                "forbidden_type",
            )

    ext = _ext(filename)
    if ext not in _ALLOWED_EXT:
        raise FileRejected(
            f"Unsupported file type '{ext or '(none)'}'. "
            "Upload CSV, Excel (.xlsx/.xls), PDF, or an image.",
            "unsupported_type",
        )

    # 2) Detect by signature.
    detected = None
    for label, sig in _SIGNATURES:
        if head.startswith(sig):
            detected = label
            break

    # Text formats (csv/tsv/txt) have no signature — accept if it decodes as text.
    if detected is None:
        if ext in (".csv", ".tsv", ".txt"):
            try:
                content[:4096].decode("utf-8")
            except UnicodeDecodeError:
                try:
                    content[:4096].decode("latin-1")
                except UnicodeDecodeError:
                    raise FileRejected(
                        "This doesn't look like a readable text/CSV file.",
                        "type_mismatch",
                    )
            detected = "text"
        else:
            raise FileRejected(
                "The file's contents don't match its extension. "
                "Re-export it and try again.",
                "type_mismatch",
            )

    # 3) Cross-check: declared extension must be consistent with detected bytes.
    _assert_consistent(ext, detected)

    return GuardReport(filename=filename, detected=detected, size_bytes=len(content))


def _assert_consistent(ext: str, detected: str) -> None:
    ok = {
        ".xlsx": {"xlsx/zip"},
        ".xls": {"xls/ole2", "xlsx/zip"},  # some .xls are actually xlsx
        ".pdf": {"pdf"},
        ".png": {"png"},
        ".jpg": {"jpg"},
        ".jpeg": {"jpg"},
        ".csv": {"text"},
        ".tsv": {"text"},
        ".txt": {"text"},
    }.get(ext)
    if ok and detected not in ok:
        raise FileRejected(
            "The file's contents don't match its extension. Re-export it and try again.",
            "type_mismatch",
        )


def sanitise_cell(value):
    """Neutralise spreadsheet formula-injection in a single cell value.

    A leading ``=``/``+``/``-``/``@`` (optionally after whitespace) makes Excel and
    Google Sheets execute the cell on open. We prefix such values with a single
    quote so they render as literal text. Non-strings pass through unchanged.
    Returns ``(safe_value, was_changed)``.
    """
    if not isinstance(value, str):
        return value, False
    stripped = value.lstrip()
    if stripped[:1] in ("=", "+", "-", "@") or stripped[:1] in ("\t", "\r"):
        return "'" + value, True
    return value, False


def scan_text_for_injection(text: str) -> int:
    """Count prompt-injection signals in a blob of text (0 = clean).

    Zero-width characters are stripped first so invisible-character splitting
    can't sneak a trigger phrase past the patterns. Hits FLAG a row for manual
    review — they never block the upload.
    """
    if not text:
        return 0
    text = text.translate(_ZERO_WIDTH)
    return sum(1 for pat in _INJECTION_PATTERNS if pat.search(text))


def sanitise_rows(rows: list[dict]) -> tuple[list[dict], int, int]:
    """Scrub a batch of parsed rows before they reach the LLM mapper.

    * formula-injection cells are quoted (Excel won't execute them on re-export)
    * prompt-injection phrases are flagged (counted) so the orchestrator can lower
      confidence / force review rather than silently trusting hostile text

    Returns ``(clean_rows, formula_cells_sanitised, injection_hits)``.
    """
    clean: list[dict] = []
    formula_hits = 0
    injection_hits = 0
    for row in rows:
        new_row = {}
        for k, v in row.items():
            safe, changed = sanitise_cell(v)
            if changed:
                formula_hits += 1
            if isinstance(safe, str):
                injection_hits += scan_text_for_injection(safe)
            new_row[k] = safe
        clean.append(new_row)
    return clean, formula_hits, injection_hits
