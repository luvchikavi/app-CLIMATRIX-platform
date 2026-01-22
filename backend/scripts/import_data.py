#!/usr/bin/env python3
"""
CLIMATRIX Data Import Script

Imports user data from JSON export file into the new system.

Usage:
    python scripts/import_data.py --input data_export.json
    python scripts/import_data.py --input data_export.json --dry-run  # Preview only
    python scripts/import_data.py --input data_export.json --skip-existing  # Skip if exists

Prerequisites:
    - Database schema must be initialized (alembic upgrade head)
    - Reference data must be seeded (python -m app.cli.seed)

Imports:
    - Organizations
    - Users (with hashed passwords preserved)
    - Sites
    - Reporting Periods
    - Activities
    - Emissions
    - Import Batches

Note: Emission factor IDs in activities/emissions will be remapped to new system factors.
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import typer
from sqlmodel import Session, create_engine, select

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.models.core import Organization, User, Site, ReportingPeriod, UserRole
from app.models.emission import (
    Activity, Emission, ImportBatch, EmissionFactor,
    CalculationMethod, DataSource, ConfidenceLevel, ImportBatchStatus
)


app = typer.Typer(help="Import CLIMATRIX data from export file")


def parse_date(value: str) -> date:
    """Parse ISO date string."""
    if not value:
        return None
    if "T" in value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    return date.fromisoformat(value)


def parse_datetime(value: str) -> datetime:
    """Parse ISO datetime string."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_uuid(value: str) -> UUID:
    """Parse UUID string."""
    if not value:
        return None
    return UUID(value)


def find_emission_factor(
    session: Session,
    activity_key: str,
    region: str = "Global",
    year: int = 2024
) -> Optional[UUID]:
    """Find matching emission factor in new system."""
    # Try exact match first
    factor = session.exec(
        select(EmissionFactor)
        .where(EmissionFactor.activity_key == activity_key)
        .where(EmissionFactor.region == region)
        .where(EmissionFactor.year == year)
        .where(EmissionFactor.is_active == True)
    ).first()

    if factor:
        return factor.id

    # Try global region
    factor = session.exec(
        select(EmissionFactor)
        .where(EmissionFactor.activity_key == activity_key)
        .where(EmissionFactor.region == "Global")
        .where(EmissionFactor.is_active == True)
    ).first()

    if factor:
        return factor.id

    # Try any matching activity_key
    factor = session.exec(
        select(EmissionFactor)
        .where(EmissionFactor.activity_key == activity_key)
        .where(EmissionFactor.is_active == True)
    ).first()

    return factor.id if factor else None


def import_organizations(session: Session, data: list[dict], skip_existing: bool) -> dict:
    """Import organizations. Returns mapping of old_id -> new_id."""
    id_map = {}
    imported = 0
    skipped = 0

    for org_data in data:
        org_id = parse_uuid(org_data["id"])

        # Check if exists
        existing = session.get(Organization, org_id)
        if existing:
            if skip_existing:
                id_map[str(org_id)] = str(org_id)
                skipped += 1
                continue
            else:
                raise ValueError(f"Organization {org_id} already exists")

        org = Organization(
            id=org_id,
            name=org_data["name"],
            country_code=org_data.get("country_code"),
            industry_code=org_data.get("industry_code"),
            base_year=org_data.get("base_year"),
            default_region=org_data.get("default_region", "Global"),
            is_active=org_data.get("is_active", True),
            created_at=parse_datetime(org_data.get("created_at")) or datetime.utcnow(),
        )
        session.add(org)
        id_map[str(org_id)] = str(org_id)
        imported += 1

    return {"id_map": id_map, "imported": imported, "skipped": skipped}


def import_users(session: Session, data: list[dict], skip_existing: bool) -> dict:
    """Import users with preserved password hashes."""
    id_map = {}
    imported = 0
    skipped = 0

    for user_data in data:
        user_id = parse_uuid(user_data["id"])

        # Check if exists
        existing = session.get(User, user_id)
        if existing:
            if skip_existing:
                id_map[str(user_id)] = str(user_id)
                skipped += 1
                continue
            else:
                raise ValueError(f"User {user_id} already exists")

        user = User(
            id=user_id,
            organization_id=parse_uuid(user_data["organization_id"]),
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            hashed_password=user_data["hashed_password"],  # Preserved!
            role=UserRole(user_data.get("role", "viewer")),
            is_active=user_data.get("is_active", True),
            created_at=parse_datetime(user_data.get("created_at")) or datetime.utcnow(),
            last_login=parse_datetime(user_data.get("last_login")),
        )
        session.add(user)
        id_map[str(user_id)] = str(user_id)
        imported += 1

    return {"id_map": id_map, "imported": imported, "skipped": skipped}


def import_sites(session: Session, data: list[dict], skip_existing: bool) -> dict:
    """Import sites."""
    id_map = {}
    imported = 0
    skipped = 0

    for site_data in data:
        site_id = parse_uuid(site_data["id"])

        # Check if exists
        existing = session.get(Site, site_id)
        if existing:
            if skip_existing:
                id_map[str(site_id)] = str(site_id)
                skipped += 1
                continue
            else:
                raise ValueError(f"Site {site_id} already exists")

        site = Site(
            id=site_id,
            organization_id=parse_uuid(site_data["organization_id"]),
            name=site_data["name"],
            country_code=site_data.get("country_code"),
            address=site_data.get("address"),
            grid_region=site_data.get("grid_region"),
            is_active=site_data.get("is_active", True),
            created_at=parse_datetime(site_data.get("created_at")) or datetime.utcnow(),
        )
        session.add(site)
        id_map[str(site_id)] = str(site_id)
        imported += 1

    return {"id_map": id_map, "imported": imported, "skipped": skipped}


def import_reporting_periods(session: Session, data: list[dict], skip_existing: bool) -> dict:
    """Import reporting periods."""
    id_map = {}
    imported = 0
    skipped = 0

    for period_data in data:
        period_id = parse_uuid(period_data["id"])

        # Check if exists
        existing = session.get(ReportingPeriod, period_id)
        if existing:
            if skip_existing:
                id_map[str(period_id)] = str(period_id)
                skipped += 1
                continue
            else:
                raise ValueError(f"ReportingPeriod {period_id} already exists")

        period = ReportingPeriod(
            id=period_id,
            organization_id=parse_uuid(period_data["organization_id"]),
            name=period_data["name"],
            start_date=parse_date(period_data["start_date"]),
            end_date=parse_date(period_data["end_date"]),
            is_locked=period_data.get("is_locked", False),
            created_at=parse_datetime(period_data.get("created_at")) or datetime.utcnow(),
        )
        session.add(period)
        id_map[str(period_id)] = str(period_id)
        imported += 1

    return {"id_map": id_map, "imported": imported, "skipped": skipped}


def import_import_batches(session: Session, data: list[dict], skip_existing: bool) -> dict:
    """Import import batches."""
    id_map = {}
    imported = 0
    skipped = 0

    for batch_data in data:
        batch_id = parse_uuid(batch_data["id"])

        # Check if exists
        existing = session.get(ImportBatch, batch_id)
        if existing:
            if skip_existing:
                id_map[str(batch_id)] = str(batch_id)
                skipped += 1
                continue
            else:
                raise ValueError(f"ImportBatch {batch_id} already exists")

        batch = ImportBatch(
            id=batch_id,
            organization_id=parse_uuid(batch_data["organization_id"]),
            reporting_period_id=parse_uuid(batch_data["reporting_period_id"]),
            file_name=batch_data["file_name"],
            file_type=batch_data.get("file_type", "excel"),
            file_size_bytes=batch_data.get("file_size_bytes"),
            status=ImportBatchStatus(batch_data.get("status", "completed")),
            total_rows=batch_data.get("total_rows", 0),
            successful_rows=batch_data.get("successful_rows", 0),
            failed_rows=batch_data.get("failed_rows", 0),
            skipped_rows=batch_data.get("skipped_rows", 0),
            error_message=batch_data.get("error_message"),
            row_errors=batch_data.get("row_errors"),
            uploaded_by=parse_uuid(batch_data["uploaded_by"]),
            uploaded_at=parse_datetime(batch_data.get("uploaded_at")) or datetime.utcnow(),
            completed_at=parse_datetime(batch_data.get("completed_at")),
        )
        session.add(batch)
        id_map[str(batch_id)] = str(batch_id)
        imported += 1

    return {"id_map": id_map, "imported": imported, "skipped": skipped}


def import_activities(session: Session, data: list[dict], skip_existing: bool) -> dict:
    """Import activities."""
    id_map = {}
    imported = 0
    skipped = 0

    for activity_data in data:
        activity_id = parse_uuid(activity_data["id"])

        # Check if exists
        existing = session.get(Activity, activity_id)
        if existing:
            if skip_existing:
                id_map[str(activity_id)] = str(activity_id)
                skipped += 1
                continue
            else:
                raise ValueError(f"Activity {activity_id} already exists")

        activity = Activity(
            id=activity_id,
            organization_id=parse_uuid(activity_data["organization_id"]),
            reporting_period_id=parse_uuid(activity_data["reporting_period_id"]),
            site_id=parse_uuid(activity_data.get("site_id")),
            scope=activity_data["scope"],
            category_code=activity_data["category_code"],
            description=activity_data.get("description", ""),
            activity_key=activity_data["activity_key"],
            quantity=activity_data["quantity"],
            unit=activity_data["unit"],
            calculation_method=CalculationMethod(activity_data.get("calculation_method", "activity")),
            activity_date=parse_date(activity_data["activity_date"]),
            data_source=DataSource(activity_data.get("data_source", "manual")),
            import_batch_id=parse_uuid(activity_data.get("import_batch_id")),
            created_by=parse_uuid(activity_data.get("created_by")),
            created_at=parse_datetime(activity_data.get("created_at")) or datetime.utcnow(),
            updated_at=parse_datetime(activity_data.get("updated_at")),
        )
        session.add(activity)
        id_map[str(activity_id)] = str(activity_id)
        imported += 1

    return {"id_map": id_map, "imported": imported, "skipped": skipped}


def import_emissions(
    session: Session,
    data: list[dict],
    activities_data: list[dict],
    skip_existing: bool
) -> dict:
    """Import emissions with remapped emission factor IDs."""
    # Build activity_key lookup
    activity_keys = {a["id"]: a["activity_key"] for a in activities_data}

    imported = 0
    skipped = 0
    factor_remapped = 0

    for emission_data in data:
        emission_id = parse_uuid(emission_data["id"])
        activity_id = str(emission_data["activity_id"])

        # Check if exists
        existing = session.get(Emission, emission_id)
        if existing:
            if skip_existing:
                skipped += 1
                continue
            else:
                raise ValueError(f"Emission {emission_id} already exists")

        # Find new emission factor
        activity_key = activity_keys.get(activity_id)
        new_factor_id = None
        if activity_key:
            new_factor_id = find_emission_factor(session, activity_key)
            if new_factor_id:
                factor_remapped += 1

        # If no factor found, use original (might fail FK constraint)
        factor_id = new_factor_id or parse_uuid(emission_data.get("emission_factor_id"))

        emission = Emission(
            id=emission_id,
            activity_id=parse_uuid(emission_data["activity_id"]),
            emission_factor_id=factor_id,
            co2_kg=emission_data.get("co2_kg"),
            ch4_kg=emission_data.get("ch4_kg"),
            n2o_kg=emission_data.get("n2o_kg"),
            co2e_kg=emission_data["co2e_kg"],
            wtt_co2e_kg=emission_data.get("wtt_co2e_kg"),
            converted_quantity=emission_data.get("converted_quantity"),
            converted_unit=emission_data.get("converted_unit"),
            formula=emission_data.get("formula"),
            confidence=ConfidenceLevel(emission_data.get("confidence", "high")),
            resolution_strategy=emission_data.get("resolution_strategy", "exact"),
            needs_review=emission_data.get("needs_review", False),
            warnings=emission_data.get("warnings"),
            calculated_at=parse_datetime(emission_data.get("calculated_at")) or datetime.utcnow(),
            recalculated_at=parse_datetime(emission_data.get("recalculated_at")),
        )
        session.add(emission)
        imported += 1

    return {"imported": imported, "skipped": skipped, "factor_remapped": factor_remapped}


@app.command()
def import_data(
    input_file: str = typer.Option(..., "--input", "-i", help="Input JSON file path"),
    database_url: Optional[str] = typer.Option(None, "--database-url", help="Override database URL"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview import without committing"),
    skip_existing: bool = typer.Option(False, "--skip-existing", help="Skip records that already exist"),
):
    """Import data from JSON export file."""

    # Load export file
    input_path = Path(input_file)
    if not input_path.exists():
        typer.echo(f"Error: File not found: {input_file}")
        raise typer.Exit(1)

    with open(input_path) as f:
        export = json.load(f)

    typer.echo(f"Loading export file: {input_path}")
    typer.echo(f"Export version: {export.get('version')}")
    typer.echo(f"Exported at: {export.get('exported_at')}")
    typer.echo(f"Source: {export.get('source_system')}")
    typer.echo()

    # Show counts
    counts = export.get("counts", {})
    typer.echo("Records to import:")
    for table, count in counts.items():
        typer.echo(f"  {table}: {count}")
    typer.echo()

    if dry_run:
        typer.echo("DRY RUN - No changes will be made")
        return

    # Create database connection
    db_url = database_url or settings.database_url

    # Handle sync vs async URL
    if "aiosqlite" in db_url:
        db_url = db_url.replace("sqlite+aiosqlite", "sqlite")
    elif "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")

    engine = create_engine(db_url)
    data = export["data"]

    with Session(engine) as session:
        try:
            typer.echo("Importing organizations...")
            result = import_organizations(session, data.get("organizations", []), skip_existing)
            typer.echo(f"  Imported: {result['imported']}, Skipped: {result['skipped']}")

            typer.echo("Importing users...")
            result = import_users(session, data.get("users", []), skip_existing)
            typer.echo(f"  Imported: {result['imported']}, Skipped: {result['skipped']}")

            typer.echo("Importing sites...")
            result = import_sites(session, data.get("sites", []), skip_existing)
            typer.echo(f"  Imported: {result['imported']}, Skipped: {result['skipped']}")

            typer.echo("Importing reporting periods...")
            result = import_reporting_periods(session, data.get("reporting_periods", []), skip_existing)
            typer.echo(f"  Imported: {result['imported']}, Skipped: {result['skipped']}")

            typer.echo("Importing import batches...")
            result = import_import_batches(session, data.get("import_batches", []), skip_existing)
            typer.echo(f"  Imported: {result['imported']}, Skipped: {result['skipped']}")

            typer.echo("Importing activities...")
            result = import_activities(session, data.get("activities", []), skip_existing)
            typer.echo(f"  Imported: {result['imported']}, Skipped: {result['skipped']}")

            typer.echo("Importing emissions...")
            result = import_emissions(
                session,
                data.get("emissions", []),
                data.get("activities", []),
                skip_existing
            )
            typer.echo(f"  Imported: {result['imported']}, Skipped: {result['skipped']}")
            typer.echo(f"  Emission factors remapped: {result['factor_remapped']}")

            session.commit()
            typer.echo("\nImport complete!")

        except Exception as e:
            session.rollback()
            typer.echo(f"\nError during import: {e}")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
