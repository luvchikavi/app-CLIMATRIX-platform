#!/usr/bin/env python3
"""
CLIMATRIX Data Export Script

Exports user data from the current system to JSON format for migration.

Usage:
    python scripts/export_data.py --output data_export.json
    python scripts/export_data.py --output data_export.json --org-id <uuid>  # Single org

Exports:
    - Organizations
    - Users (with hashed passwords)
    - Sites
    - Reporting Periods
    - Activities
    - Emissions
    - Import Batches

Note: Emission factors and reference data are NOT exported (will be freshly seeded).
"""
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

import typer
from sqlmodel import Session, create_engine, select

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.models.core import Organization, User, Site, ReportingPeriod
from app.models.emission import Activity, Emission, ImportBatch


app = typer.Typer(help="Export CLIMATRIX data for migration")


def serialize_value(value):
    """Convert value to JSON-serializable format."""
    if value is None:
        return None
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, list):
        return [serialize_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    elif hasattr(value, 'value'):  # Enum
        return value.value
    else:
        return value


def model_to_dict(model) -> dict:
    """Convert SQLModel to dictionary."""
    return {
        key: serialize_value(getattr(model, key))
        for key in model.model_fields.keys()
        if hasattr(model, key)
    }


def export_organizations(session: Session, org_id: Optional[UUID] = None) -> list[dict]:
    """Export organizations."""
    query = select(Organization)
    if org_id:
        query = query.where(Organization.id == org_id)

    orgs = session.exec(query).all()
    return [model_to_dict(org) for org in orgs]


def export_users(session: Session, org_id: Optional[UUID] = None) -> list[dict]:
    """Export users with hashed passwords."""
    query = select(User)
    if org_id:
        query = query.where(User.organization_id == org_id)

    users = session.exec(query).all()
    return [model_to_dict(user) for user in users]


def export_sites(session: Session, org_id: Optional[UUID] = None) -> list[dict]:
    """Export sites."""
    query = select(Site)
    if org_id:
        query = query.where(Site.organization_id == org_id)

    sites = session.exec(query).all()
    return [model_to_dict(site) for site in sites]


def export_reporting_periods(session: Session, org_id: Optional[UUID] = None) -> list[dict]:
    """Export reporting periods."""
    query = select(ReportingPeriod)
    if org_id:
        query = query.where(ReportingPeriod.organization_id == org_id)

    periods = session.exec(query).all()
    return [model_to_dict(period) for period in periods]


def export_import_batches(session: Session, org_id: Optional[UUID] = None) -> list[dict]:
    """Export import batches."""
    query = select(ImportBatch)
    if org_id:
        query = query.where(ImportBatch.organization_id == org_id)

    batches = session.exec(query).all()
    return [model_to_dict(batch) for batch in batches]


def export_activities(session: Session, org_id: Optional[UUID] = None) -> list[dict]:
    """Export activities."""
    query = select(Activity)
    if org_id:
        query = query.where(Activity.organization_id == org_id)

    activities = session.exec(query).all()
    return [model_to_dict(activity) for activity in activities]


def export_emissions(session: Session, activity_ids: list[str]) -> list[dict]:
    """Export emissions for given activity IDs."""
    if not activity_ids:
        return []

    query = select(Emission).where(
        Emission.activity_id.in_([UUID(aid) for aid in activity_ids])
    )
    emissions = session.exec(query).all()
    return [model_to_dict(emission) for emission in emissions]


@app.command()
def export_data(
    output: str = typer.Option(..., "--output", "-o", help="Output JSON file path"),
    org_id: Optional[str] = typer.Option(None, "--org-id", help="Export single organization by ID"),
    database_url: Optional[str] = typer.Option(None, "--database-url", help="Override database URL"),
):
    """Export all user data to JSON file."""

    # Create database connection
    db_url = database_url or settings.database_url

    # Handle sync vs async URL
    if "aiosqlite" in db_url:
        db_url = db_url.replace("sqlite+aiosqlite", "sqlite")
    elif "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")

    engine = create_engine(db_url)

    typer.echo(f"Connecting to database...")
    typer.echo(f"URL: {db_url[:50]}...")

    org_uuid = UUID(org_id) if org_id else None

    with Session(engine) as session:
        typer.echo("Exporting organizations...")
        organizations = export_organizations(session, org_uuid)
        typer.echo(f"  Found {len(organizations)} organizations")

        typer.echo("Exporting users...")
        users = export_users(session, org_uuid)
        typer.echo(f"  Found {len(users)} users")

        typer.echo("Exporting sites...")
        sites = export_sites(session, org_uuid)
        typer.echo(f"  Found {len(sites)} sites")

        typer.echo("Exporting reporting periods...")
        reporting_periods = export_reporting_periods(session, org_uuid)
        typer.echo(f"  Found {len(reporting_periods)} reporting periods")

        typer.echo("Exporting import batches...")
        import_batches = export_import_batches(session, org_uuid)
        typer.echo(f"  Found {len(import_batches)} import batches")

        typer.echo("Exporting activities...")
        activities = export_activities(session, org_uuid)
        typer.echo(f"  Found {len(activities)} activities")

        typer.echo("Exporting emissions...")
        activity_ids = [a["id"] for a in activities]
        emissions = export_emissions(session, activity_ids)
        typer.echo(f"  Found {len(emissions)} emissions")

    # Build export data
    export = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "source_system": "CLIMATERIX",
        "target_system": "CLIMATRIX",
        "data": {
            "organizations": organizations,
            "users": users,
            "sites": sites,
            "reporting_periods": reporting_periods,
            "import_batches": import_batches,
            "activities": activities,
            "emissions": emissions,
        },
        "counts": {
            "organizations": len(organizations),
            "users": len(users),
            "sites": len(sites),
            "reporting_periods": len(reporting_periods),
            "import_batches": len(import_batches),
            "activities": len(activities),
            "emissions": len(emissions),
        }
    }

    # Write to file
    output_path = Path(output)
    with open(output_path, "w") as f:
        json.dump(export, f, indent=2)

    typer.echo(f"\nExport complete!")
    typer.echo(f"Output file: {output_path.absolute()}")
    typer.echo(f"Total records: {sum(export['counts'].values())}")


if __name__ == "__main__":
    app()
