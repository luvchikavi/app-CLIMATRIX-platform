"""
Core domain models: Organization, User, Site, ReportingPeriod.
These form the multi-tenant foundation of the application.
"""
from datetime import datetime, date
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.emission import Activity


class UserRole(str, Enum):
    """User roles for access control."""
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class OrganizationBase(SQLModel):
    """Base fields for Organization."""
    name: str = Field(max_length=255, index=True)
    country_code: Optional[str] = Field(default=None, max_length=2)
    industry_code: Optional[str] = Field(default=None, max_length=20)
    base_year: Optional[int] = Field(default=None)
    default_region: str = Field(default="Global", max_length=50)


class Organization(OrganizationBase, table=True):
    """
    Organization (tenant) model.
    All data is scoped to an organization for multi-tenancy.
    """
    __tablename__ = "organizations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    users: list["User"] = Relationship(back_populates="organization")
    sites: list["Site"] = Relationship(back_populates="organization")
    reporting_periods: list["ReportingPeriod"] = Relationship(back_populates="organization")


class UserBase(SQLModel):
    """Base fields for User."""
    email: str = Field(max_length=255, unique=True, index=True)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.VIEWER)
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    """
    User model with authentication and organization membership.
    """
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    organization: Organization = Relationship(back_populates="users")


class SiteBase(SQLModel):
    """Base fields for Site/Facility."""
    name: str = Field(max_length=255)
    country_code: Optional[str] = Field(default=None, max_length=2)
    address: Optional[str] = Field(default=None, max_length=500)
    grid_region: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)


class Site(SiteBase, table=True):
    """
    Site/Facility model for location-specific emissions tracking.
    """
    __tablename__ = "sites"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    organization: Organization = Relationship(back_populates="sites")
    activities: list["Activity"] = Relationship(back_populates="site")


class ReportingPeriodBase(SQLModel):
    """Base fields for ReportingPeriod."""
    name: str = Field(max_length=100)  # e.g., "Q1 2024", "FY 2024"
    start_date: date
    end_date: date
    is_locked: bool = Field(default=False)


class ReportingPeriod(ReportingPeriodBase, table=True):
    """
    Reporting period for organizing activity data.
    Activities belong to a specific reporting period.
    """
    __tablename__ = "reporting_periods"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    organization: Organization = Relationship(back_populates="reporting_periods")
    activities: list["Activity"] = Relationship(back_populates="reporting_period")
