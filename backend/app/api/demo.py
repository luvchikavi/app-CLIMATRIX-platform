"""Public "Try Climatrix" demo endpoint — the marketing-site trust builder.

    POST /api/demo/analyze   upload any spreadsheet -> instant, EXPLAINED emissions

No auth, no persistence. A prospect drops a CSV/Excel and immediately sees credible
numbers WITH the methodology behind them (which emission factor, its source, the
formula). It reuses the exact same ingestion + calculation services the real app
uses — so the demo numbers are the product's numbers, not a mock.

Guard rails that make this safe to expose publicly:
  * the file-upload security guard runs before a byte is parsed
  * work is CAPPED at ~50 rows across all sheets (a demo, not a full import)
  * per-IP rate limiting via the shared slowapi limiter
  * nothing is written to the database — the session is read-only and rolled back
"""

from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.rate_limit import limiter
from app.services.calculation import ActivityInput, CalculationPipeline
from app.services.calculation.pipeline import CalculationError
from app.services.calculation.normalizer import UnitConversionError
from app.services.calculation.resolver import FactorNotFoundError
from app.services.ingestion import catalog as catalog_mod
from app.services.ingestion.file_guard import FileRejected, check_upload
from app.services.ingestion.fast_mapper import map_table_fast
from app.services.ingestion.grounding import ground_row
from app.services.ingestion.loader import load
from app.services.ingestion.mapper import map_table

router = APIRouter()

# Hard cap on the work a single anonymous demo request can trigger. This is a
# taster, not the real importer — 50 rows is plenty to prove credibility while
# keeping every request cheap (and the LLM bill bounded).
_MAX_DEMO_ROWS = 50

# Demo uploads are deliberately small — a prospect's sample file, not a full year
# of data. Cap well under the app-wide limit to keep parsing snappy and cheap.
_MAX_DEMO_BYTES = 5 * 1024 * 1024  # 5 MB

# Public endpoint — rate-limit hard by IP. Reuses the shared limiter (in-memory in
# dev/test, Redis in prod) exactly like the authenticated routers do.
_DEMO_RATE_LIMIT = "5/minute"


# ---------------------------------------------------------------------------
# response schemas
# ---------------------------------------------------------------------------


class Methodology(BaseModel):
    """The "show your work" payload — why this number is what it is."""

    factor_value: Optional[float]
    factor_unit: Optional[str]
    factor_source: Optional[str]  # e.g. DEFRA, IEA, EPA
    factor_year: Optional[int]
    factor_region: Optional[str]
    formula: Optional[str]
    resolution_strategy: Optional[str]
    confidence: Optional[str]


class DemoRow(BaseModel):
    sheet: str
    source_description: str
    activity_key: Optional[str]
    scope: Optional[int]
    category: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    co2e_kg: Optional[float]
    methodology: Optional[Methodology]
    note: Optional[str] = None  # why a row couldn't be calculated, if so


class ScopeTotal(BaseModel):
    scope: int
    tco2e: float


class DemoResult(BaseModel):
    filename: str
    rows_read: int
    rows_calculated: int
    capped: bool  # True if the file had more rows than the demo cap
    total_tco2e: float
    by_scope: list[ScopeTotal]
    rows: list[DemoRow]
    notice: Optional[str] = None  # human-readable explanation when nothing lands


# ---------------------------------------------------------------------------
# endpoint
# ---------------------------------------------------------------------------


@router.post("/demo/analyze", response_model=DemoResult)
@limiter.limit(_DEMO_RATE_LIMIT)
async def analyze_demo(
    request: Request,
    file: UploadFile = File(...),
    session: Annotated[AsyncSession, Depends(get_session)] = None,
):
    """Parse an uploaded spreadsheet and return EXPLAINED emission results.

    Public, no auth, nothing persisted. Runs the real ingestion parser + the real
    calculation pipeline in memory, capped at ~50 rows.
    """
    content = await file.read()

    # 1) Security guard — reject unsafe/oversized/mismatched files before parsing.
    try:
        report = check_upload(
            content, file.filename or "upload", max_bytes=_MAX_DEMO_BYTES
        )
    except FileRejected as exc:
        raise HTTPException(status_code=400, detail=exc.message)

    # 2) Load into normalized tables (CSV/XLSX). PDF/image need the vision path.
    try:
        tables = load(content, report.filename)
    except NotImplementedError:
        raise HTTPException(
            status_code=400,
            detail=(
                "This demo reads spreadsheets (CSV or Excel). For PDFs and images, "
                "sign up for a full account."
            ),
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="We couldn't read that file. Try a CSV or Excel export.",
        )

    if not tables:
        return DemoResult(
            filename=report.filename,
            rows_read=0,
            rows_calculated=0,
            capped=False,
            total_tco2e=0.0,
            by_scope=[],
            rows=[],
            notice=(
                "We opened your file but found no data rows — every sheet looked "
                "empty or like instructions. Add some rows and try again."
            ),
        )

    # 3) Build the factor catalog from the live DB (read-only).
    cat = await catalog_mod.build_from_db(session)

    # 4) Map rows sheet by sheet (fast mapper: ~2 LLM calls/sheet), stopping once
    #    we've mapped the demo cap. mapped_source is the raw mapper output.
    mapped_source: list[tuple[str, object]] = []  # (sheet_name, MappedRow)
    rows_read = 0
    capped = False
    for table in tables:
        remaining = _MAX_DEMO_ROWS - len(mapped_source)
        if remaining <= 0:
            capped = True
            break
        try:
            mapped_rows = map_table_fast(table, cat, max_rows=remaining, client=None)
        except Exception:
            # Fall back to the slower row mapper; skip a sheet that still fails so
            # one bad sheet never sinks the whole demo.
            try:
                mapped_rows = map_table(table, cat, max_rows=remaining, client=None)
            except Exception:
                continue
        rows_read += len(mapped_rows)
        for m in mapped_rows:
            if len(mapped_source) >= _MAX_DEMO_ROWS:
                capped = True
                break
            mapped_source.append((table.sheet, m))

    # 5) Calculate each mapped row through the REAL pipeline (in memory only).
    pipeline = CalculationPipeline(session)
    out_rows: list[DemoRow] = []
    scope_totals: dict[int, float] = {}
    total_kg = 0.0
    calculated = 0

    for sheet, m in mapped_source:
        base = DemoRow(
            sheet=sheet or "",
            source_description=m.description or "",
            activity_key=m.activity_key,
            scope=m.scope,
            category=m.category_code,
            quantity=m.quantity,
            unit=m.unit,
            co2e_kg=None,
            methodology=None,
        )

        # Only rows the mapper could fully ground are worth calculating. Everything
        # else is shown as "needs confirmation" rather than silently dropped.
        if (
            not m.activity_key
            or m.quantity is None
            or not m.unit
            or m.scope not in (1, 2, 3)
            or not m.category_code
        ):
            base.note = (
                "Couldn't confidently match this to an activity — in the full app "
                "you'd confirm it in one click."
            )
            out_rows.append(base)
            continue

        # Grounding is the cheap, deterministic pre-check the real importer uses; if
        # it won't resolve, skip the (more expensive) calculation and explain why.
        grounding = await ground_row(
            session, m.activity_key, m.unit or "", region="Global", year=2024
        )
        if not grounding.ok:
            base.note = grounding.reason
            out_rows.append(base)
            continue

        try:
            calc = await pipeline.calculate(
                ActivityInput(
                    activity_key=m.activity_key,
                    quantity=Decimal(str(m.quantity)),
                    unit=m.unit,
                    scope=m.scope,
                    category_code=m.category_code,
                    region="Global",
                    year=2024,
                )
            )
        except (FactorNotFoundError, UnitConversionError, CalculationError) as exc:
            base.note = f"Not calculated: {exc}"[:300]
            out_rows.append(base)
            continue
        except Exception:
            base.note = "Not calculated: this row needs manual review."
            out_rows.append(base)
            continue

        co2e = float(calc.co2e_kg)
        base.co2e_kg = round(co2e, 4)
        base.methodology = Methodology(
            factor_value=(float(calc.factor_value) if calc.factor_value else None),
            factor_unit=calc.factor_unit or None,
            factor_source=calc.factor_source or None,
            factor_year=calc.factor_year,
            factor_region=calc.factor_region or None,
            formula=calc.formula or None,
            resolution_strategy=calc.resolution_strategy or None,
            confidence=calc.confidence or None,
        )
        out_rows.append(base)

        total_kg += co2e
        scope_totals[m.scope] = scope_totals.get(m.scope, 0.0) + co2e
        calculated += 1

    # 6) Never persist anything the demo touched (catalog build / resolver reads
    #    don't write, but roll back defensively so a demo can't leak into the DB).
    try:
        await session.rollback()
    except Exception:
        pass

    by_scope = [
        ScopeTotal(scope=s, tco2e=round(kg / 1000.0, 6))
        for s, kg in sorted(scope_totals.items())
    ]

    notice = None
    if calculated == 0:
        notice = (
            "We read your file but couldn't auto-calculate any rows yet. In the full "
            "app you'd confirm the highlighted rows and get instant numbers."
        )

    return DemoResult(
        filename=report.filename,
        rows_read=rows_read,
        rows_calculated=calculated,
        capped=capped,
        total_tco2e=round(total_kg / 1000.0, 6),
        by_scope=by_scope,
        rows=out_rows,
        notice=notice,
    )
