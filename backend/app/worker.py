"""
Arq Background Worker Configuration.

Processes async jobs like file imports, bulk recalculations, and report generation.

To run the worker:
    arq app.worker.WorkerSettings

Or with more workers:
    arq app.worker.WorkerSettings --watch
"""
import asyncio
import csv
import io
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.jobs import ImportJob, JobStatus
from app.models.emission import Activity, Emission, DataSource
from app.models.core import ReportingPeriod
from app.services.calculation import CalculationPipeline, ActivityInput
from app.services.ai import ColumnMapper, DataExtractor, DataValidator


# =============================================================================
# Database Session Factory
# =============================================================================

def get_async_session_factory():
    """Create async session factory for worker."""
    engine = create_async_engine(settings.database_url, echo=settings.database_echo)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# =============================================================================
# Import Job Processor
# =============================================================================

async def process_import_job(ctx: dict, job_id: str) -> dict:
    """
    Process a file import job asynchronously.

    Args:
        ctx: Arq context (contains Redis connection)
        job_id: UUID of the ImportJob to process

    Returns:
        dict with job results
    """
    session_factory = get_async_session_factory()

    async with session_factory() as session:
        # Get the job
        result = await session.execute(
            select(ImportJob).where(ImportJob.id == UUID(job_id))
        )
        job = result.scalar_one_or_none()

        if not job:
            return {"error": f"Job {job_id} not found"}

        if job.status != JobStatus.PENDING:
            return {"error": f"Job {job_id} is not pending (status: {job.status})"}

        # Mark as processing
        job.mark_started()
        await session.commit()

        try:
            # Read the file
            with open(job.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            job.total_rows = len(rows)
            await session.commit()

            # Get reporting period for validation
            period_result = await session.execute(
                select(ReportingPeriod).where(ReportingPeriod.id == job.reporting_period_id)
            )
            period = period_result.scalar_one_or_none()

            if not period:
                job.mark_failed("Reporting period not found")
                await session.commit()
                return {"error": "Reporting period not found"}

            # Process rows
            pipeline = CalculationPipeline(session)
            successful = 0
            failed = 0
            row_errors = []
            activities_created = []

            for i, row in enumerate(rows):
                try:
                    # Parse row data
                    activity_data = parse_import_row(row, job.organization_id, job.reporting_period_id)

                    # Create activity
                    activity = Activity(
                        organization_id=job.organization_id,
                        reporting_period_id=job.reporting_period_id,
                        scope=activity_data["scope"],
                        category_code=activity_data["category_code"],
                        description=activity_data["description"],
                        activity_key=activity_data["activity_key"],
                        quantity=activity_data["quantity"],
                        unit=activity_data["unit"],
                        activity_date=activity_data["activity_date"],
                        data_source=DataSource.IMPORT,
                        import_batch_id=job.id,
                        created_by=job.created_by,
                    )
                    session.add(activity)
                    await session.flush()  # Get activity ID

                    # Calculate emission
                    calc_result = await pipeline.calculate(ActivityInput(
                        activity_key=activity.activity_key,
                        quantity=activity.quantity,
                        unit=activity.unit,
                        scope=activity.scope,
                        category_code=activity.category_code,
                        region=period.organization.default_region if hasattr(period, 'organization') else "Global",
                        year=settings.default_emission_factor_year,
                    ))

                    # Create emission record
                    emission = Emission(
                        activity_id=activity.id,
                        emission_factor_id=calc_result.emission_factor_id,
                        co2_kg=calc_result.co2_kg,
                        ch4_kg=calc_result.ch4_kg,
                        n2o_kg=calc_result.n2o_kg,
                        co2e_kg=calc_result.co2e_kg,
                        wtt_co2e_kg=calc_result.wtt_co2e_kg,
                        converted_quantity=calc_result.converted_quantity,
                        converted_unit=calc_result.converted_unit,
                        formula=calc_result.formula,
                        confidence=calc_result.confidence,
                        resolution_strategy=calc_result.resolution_strategy,
                        warnings=calc_result.warnings if calc_result.warnings else None,
                    )
                    session.add(emission)

                    successful += 1
                    activities_created.append(str(activity.id))

                except Exception as e:
                    failed += 1
                    row_errors.append({
                        "row": i + 1,
                        "error": str(e),
                        "data": row
                    })

                # Update progress every 10 rows
                if (i + 1) % 10 == 0:
                    job.update_progress(i + 1, successful, failed)
                    await session.commit()

            # Final update
            job.row_errors = row_errors if row_errors else None
            job.mark_completed(
                successful=successful,
                failed=failed,
                summary={
                    "total_rows": len(rows),
                    "successful": successful,
                    "failed": failed,
                    "activities_created": len(activities_created),
                }
            )
            await session.commit()

            return {
                "job_id": job_id,
                "status": "completed",
                "successful": successful,
                "failed": failed,
            }

        except Exception as e:
            job.mark_failed(str(e))
            await session.commit()
            return {"error": str(e)}

        finally:
            # Clean up uploaded file after processing
            if job.file_path and os.path.exists(job.file_path):
                try:
                    os.remove(job.file_path)
                except OSError:
                    pass


def parse_import_row(row: dict, org_id: UUID, period_id: UUID) -> dict:
    """
    Parse a CSV row into activity data.

    Handles column aliases and validation.
    """
    # Column aliases (case-insensitive)
    aliases = {
        "scope": ["scope", "ghg_scope"],
        "category_code": ["category_code", "category", "cat_code"],
        "activity_key": ["activity_key", "activity_type", "type"],
        "description": ["description", "desc", "name"],
        "quantity": ["quantity", "amount", "value"],
        "unit": ["unit", "units", "uom"],
        "activity_date": ["activity_date", "date", "period_date"],
    }

    def get_value(row: dict, field: str) -> str:
        """Get value from row using aliases."""
        for alias in aliases.get(field, [field]):
            # Try exact match
            if alias in row:
                return row[alias]
            # Try case-insensitive
            for key in row.keys():
                if key.lower() == alias.lower():
                    return row[key]
        return None

    # Parse required fields
    scope_str = get_value(row, "scope")
    if not scope_str:
        raise ValueError("Missing 'scope' column")
    scope = int(scope_str)
    if scope not in [1, 2, 3]:
        raise ValueError(f"Invalid scope: {scope}. Must be 1, 2, or 3")

    category_code = get_value(row, "category_code")
    if not category_code:
        raise ValueError("Missing 'category_code' column")

    activity_key = get_value(row, "activity_key")
    if not activity_key:
        raise ValueError("Missing 'activity_key' column")

    description = get_value(row, "description") or activity_key

    quantity_str = get_value(row, "quantity")
    if not quantity_str:
        raise ValueError("Missing 'quantity' column")
    try:
        quantity = Decimal(str(quantity_str).replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity: {quantity_str}")

    unit = get_value(row, "unit")
    if not unit:
        raise ValueError("Missing 'unit' column")

    date_str = get_value(row, "activity_date")
    if not date_str:
        raise ValueError("Missing 'activity_date' column")
    try:
        # Try common date formats
        from datetime import datetime
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
            try:
                activity_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Invalid date format: {date_str}")
    except Exception as e:
        raise ValueError(f"Invalid date: {date_str} - {e}")

    return {
        "scope": scope,
        "category_code": category_code,
        "activity_key": activity_key,
        "description": description,
        "quantity": quantity,
        "unit": unit,
        "activity_date": activity_date,
    }


# =============================================================================
# AI-Powered Smart Import Job
# =============================================================================

async def smart_import_job(ctx: dict, job_id: str) -> dict:
    """
    Process a file import using AI for intelligent column mapping and data extraction.

    This function handles files that don't follow the standard import template:
    - Auto-detects column meanings
    - Extracts quantities and units from combined text
    - Maps to appropriate activity_keys
    - Validates data and flags issues

    Args:
        ctx: Arq context
        job_id: UUID of the ImportJob to process

    Returns:
        dict with job results including AI insights
    """
    session_factory = get_async_session_factory()
    column_mapper = ColumnMapper()
    data_extractor = DataExtractor()
    data_validator = DataValidator()

    async with session_factory() as session:
        # Get the job
        result = await session.execute(
            select(ImportJob).where(ImportJob.id == UUID(job_id))
        )
        job = result.scalar_one_or_none()

        if not job:
            return {"error": f"Job {job_id} not found"}

        if job.status != JobStatus.PENDING:
            return {"error": f"Job {job_id} is not pending (status: {job.status})"}

        # Mark as processing
        job.mark_started()
        await session.commit()

        try:
            # Read the file
            with open(job.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            headers = reader.fieldnames if reader.fieldnames else []
            job.total_rows = len(rows)

            # Phase 1: AI Column Mapping
            sample_data = [list(row.values()) for row in rows[:5]]
            mapping_result = column_mapper.map_columns(headers, sample_data)

            if not mapping_result.success:
                job.mark_failed("AI could not map columns. Please use standard template.")
                await session.commit()
                return {"error": "Column mapping failed"}

            # Store mapping info in job metadata
            job.metadata = {
                "ai_mapping": {
                    "detected_structure": mapping_result.detected_structure,
                    "date_column": mapping_result.date_column,
                    "mappings": [
                        {
                            "header": m.original_header,
                            "activity_key": m.activity_key,
                            "unit": m.detected_unit,
                            "confidence": m.confidence,
                        }
                        for m in mapping_result.mappings
                        if m.column_type == "activity"
                    ],
                    "warnings": mapping_result.warnings,
                }
            }
            await session.commit()

            # Get reporting period
            period_result = await session.execute(
                select(ReportingPeriod).where(ReportingPeriod.id == job.reporting_period_id)
            )
            period = period_result.scalar_one_or_none()

            if not period:
                job.mark_failed("Reporting period not found")
                await session.commit()
                return {"error": "Reporting period not found"}

            # Phase 2: Process rows using AI mapping
            pipeline = CalculationPipeline(session)
            successful = 0
            failed = 0
            row_errors = []
            activities_created = []

            # Build column lookup from mapping
            activity_columns = {
                m.original_header: m
                for m in mapping_result.mappings
                if m.column_type == "activity" and m.activity_key
            }

            for i, row in enumerate(rows):
                try:
                    # Extract date from date column
                    activity_date = None
                    if mapping_result.date_column and mapping_result.date_column in row:
                        date_str = row[mapping_result.date_column]
                        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m"]:
                            try:
                                activity_date = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                        if not activity_date:
                            activity_date = datetime.now().date()
                    else:
                        activity_date = datetime.now().date()

                    # Process each activity column
                    for col_name, mapping in activity_columns.items():
                        if col_name not in row:
                            continue

                        value = row[col_name]
                        if not value or str(value).strip() == "":
                            continue

                        # Try to parse quantity
                        try:
                            quantity = Decimal(str(value).replace(",", "").strip())
                        except (InvalidOperation, ValueError):
                            # Try AI extraction for complex values
                            extraction = data_extractor.extract(str(value))
                            if extraction.activities:
                                quantity = extraction.activities[0].quantity
                            else:
                                row_errors.append({
                                    "row": i + 1,
                                    "column": col_name,
                                    "error": f"Could not parse quantity: {value}",
                                })
                                failed += 1
                                continue

                        # Validate with AI
                        validation = data_validator.validate_activity({
                            "activity_key": mapping.activity_key,
                            "quantity": float(quantity),
                            "unit": mapping.detected_unit,
                        })

                        if not validation.is_valid:
                            errors_str = "; ".join(i.message for i in validation.issues if i.severity == "error")
                            row_errors.append({
                                "row": i + 1,
                                "column": col_name,
                                "error": errors_str,
                                "ai_notes": validation.ai_notes,
                            })
                            failed += 1
                            continue

                        # Create activity
                        activity = Activity(
                            organization_id=job.organization_id,
                            reporting_period_id=job.reporting_period_id,
                            scope=mapping.scope,
                            category_code=mapping.category_code,
                            description=f"{col_name}: {quantity} {mapping.detected_unit}",
                            activity_key=mapping.activity_key,
                            quantity=quantity,
                            unit=mapping.detected_unit,
                            activity_date=activity_date,
                            data_source=DataSource.IMPORT,
                            import_batch_id=job.id,
                            created_by=job.created_by,
                        )
                        session.add(activity)
                        await session.flush()

                        # Calculate emission
                        calc_result = await pipeline.calculate(ActivityInput(
                            activity_key=activity.activity_key,
                            quantity=activity.quantity,
                            unit=activity.unit,
                            scope=activity.scope,
                            category_code=activity.category_code,
                            region="Global",
                            year=settings.default_emission_factor_year,
                        ))

                        # Create emission
                        emission = Emission(
                            activity_id=activity.id,
                            emission_factor_id=calc_result.emission_factor_id,
                            co2_kg=calc_result.co2_kg,
                            ch4_kg=calc_result.ch4_kg,
                            n2o_kg=calc_result.n2o_kg,
                            co2e_kg=calc_result.co2e_kg,
                            wtt_co2e_kg=calc_result.wtt_co2e_kg,
                            converted_quantity=calc_result.converted_quantity,
                            converted_unit=calc_result.converted_unit,
                            formula=calc_result.formula,
                            confidence=calc_result.confidence,
                            resolution_strategy=calc_result.resolution_strategy,
                            warnings=calc_result.warnings if calc_result.warnings else None,
                        )
                        session.add(emission)

                        successful += 1
                        activities_created.append(str(activity.id))

                except Exception as e:
                    failed += 1
                    row_errors.append({
                        "row": i + 1,
                        "error": str(e),
                    })

                # Update progress
                if (i + 1) % 10 == 0:
                    job.update_progress(i + 1, successful, failed)
                    await session.commit()

            # Final update
            job.row_errors = row_errors if row_errors else None
            job.mark_completed(
                successful=successful,
                failed=failed,
                summary={
                    "total_rows": len(rows),
                    "successful": successful,
                    "failed": failed,
                    "activities_created": len(activities_created),
                    "ai_mapping_used": True,
                    "detected_columns": len(activity_columns),
                }
            )
            await session.commit()

            return {
                "job_id": job_id,
                "status": "completed",
                "successful": successful,
                "failed": failed,
                "ai_insights": mapping_result.ai_notes,
            }

        except Exception as e:
            job.mark_failed(str(e))
            await session.commit()
            return {"error": str(e)}

        finally:
            # Clean up uploaded file after processing
            if job.file_path and os.path.exists(job.file_path):
                try:
                    os.remove(job.file_path)
                except OSError:
                    pass


# =============================================================================
# Bulk Recalculation Job
# =============================================================================

async def recalculate_period_job(ctx: dict, period_id: str, user_id: str) -> dict:
    """
    Recalculate all emissions for a reporting period.

    Used when emission factors are updated or corrections needed.
    """
    session_factory = get_async_session_factory()

    async with session_factory() as session:
        # Get all activities for the period
        result = await session.execute(
            select(Activity).where(Activity.reporting_period_id == UUID(period_id))
        )
        activities = result.scalars().all()

        if not activities:
            return {"message": "No activities to recalculate"}

        pipeline = CalculationPipeline(session)
        recalculated = 0
        errors = []

        for activity in activities:
            try:
                # Delete existing emission
                if activity.emission:
                    await session.delete(activity.emission)

                # Recalculate
                calc_result = await pipeline.calculate(ActivityInput(
                    activity_key=activity.activity_key,
                    quantity=activity.quantity,
                    unit=activity.unit,
                    scope=activity.scope,
                    category_code=activity.category_code,
                    region="Global",
                    year=settings.default_emission_factor_year,
                ))

                # Create new emission
                emission = Emission(
                    activity_id=activity.id,
                    emission_factor_id=calc_result.emission_factor_id,
                    co2_kg=calc_result.co2_kg,
                    ch4_kg=calc_result.ch4_kg,
                    n2o_kg=calc_result.n2o_kg,
                    co2e_kg=calc_result.co2e_kg,
                    wtt_co2e_kg=calc_result.wtt_co2e_kg,
                    converted_quantity=calc_result.converted_quantity,
                    converted_unit=calc_result.converted_unit,
                    formula=calc_result.formula,
                    confidence=calc_result.confidence,
                    resolution_strategy=calc_result.resolution_strategy,
                    recalculated_at=datetime.utcnow(),
                )
                session.add(emission)
                recalculated += 1

            except Exception as e:
                errors.append({
                    "activity_id": str(activity.id),
                    "error": str(e)
                })

        await session.commit()

        return {
            "recalculated": recalculated,
            "errors": errors,
        }


# =============================================================================
# Worker Settings
# =============================================================================

class WorkerSettings:
    """Arq worker configuration."""

    # Redis connection
    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    # Job functions
    functions = [
        process_import_job,
        smart_import_job,  # AI-powered import
        recalculate_period_job,
    ]

    # Job timeout (10 minutes max per job)
    job_timeout = 600

    # Max concurrent jobs per worker
    max_jobs = 10

    # How long to keep job results
    keep_result = 3600  # 1 hour

    # Retry settings
    max_tries = 3
    retry_jobs = True

    # Health check
    health_check_interval = 30

    # Logging
    @staticmethod
    async def on_startup(ctx: dict):
        """Called when worker starts."""
        print("🚀 CLIMATRIX Worker started")
        print(f"   Redis: {settings.redis_url}")
        print(f"   Database: {settings.database_url[:50]}...")

    @staticmethod
    async def on_shutdown(ctx: dict):
        """Called when worker shuts down."""
        print("👋 CLIMATRIX Worker shutting down")
