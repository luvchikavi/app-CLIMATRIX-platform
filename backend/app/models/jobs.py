"""
Background job tracking models.

Tracks the status of async jobs like file imports.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Column, JSON


class JobStatus(str, Enum):
    """Status of a background job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Type of background job."""
    IMPORT_CSV = "import_csv"
    IMPORT_EXCEL = "import_excel"
    RECALCULATE = "recalculate"
    EXPORT_REPORT = "export_report"


class ImportJob(SQLModel, table=True):
    """
    Tracks file import jobs.

    Stores progress and results for async import processing.
    """
    __tablename__ = "import_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(index=True)
    reporting_period_id: UUID = Field(index=True)
    created_by: UUID = Field(index=True)

    # Job info
    job_type: JobType = Field(default=JobType.IMPORT_CSV)
    status: JobStatus = Field(default=JobStatus.PENDING, index=True)

    # File info
    original_filename: str
    file_path: str  # Stored file path
    file_size_bytes: Optional[int] = None

    # Progress tracking
    total_rows: Optional[int] = None
    processed_rows: int = Field(default=0)
    successful_rows: int = Field(default=0)
    failed_rows: int = Field(default=0)

    # Progress percentage (0-100)
    @property
    def progress_percent(self) -> int:
        if not self.total_rows or self.total_rows == 0:
            return 0
        return int((self.processed_rows / self.total_rows) * 100)

    # Results
    error_message: Optional[str] = None
    row_errors: Optional[list] = Field(default=None, sa_column=Column(JSON))

    # Summary of what was imported
    summary: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def mark_started(self):
        """Mark job as started."""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def mark_completed(self, successful: int, failed: int, summary: dict = None):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.successful_rows = successful
        self.failed_rows = failed
        self.summary = summary

    def mark_failed(self, error: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error

    def update_progress(self, processed: int, successful: int = None, failed: int = None):
        """Update progress counters."""
        self.processed_rows = processed
        if successful is not None:
            self.successful_rows = successful
        if failed is not None:
            self.failed_rows = failed
