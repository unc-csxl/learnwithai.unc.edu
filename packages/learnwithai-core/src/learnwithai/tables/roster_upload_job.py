"""Database-backed roster upload job tracking."""

import enum
from datetime import datetime

from sqlmodel import (
    Column,
    DateTime,
    Enum,
    Field,
    ForeignKey,
    Integer,
    SQLModel,
    Text,
    func,
)


class RosterUploadStatus(str, enum.Enum):
    """Lifecycle state of a roster CSV upload job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RosterUploadJob(SQLModel, table=True):
    """Tracks the state and results of an asynchronous roster CSV upload."""

    __tablename__ = "roster_upload_job"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id"), nullable=False),
    )
    uploaded_by_pid: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    status: RosterUploadStatus = Field(
        default=RosterUploadStatus.PENDING,
        sa_column=Column(
            Enum(
                RosterUploadStatus,
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
            server_default=RosterUploadStatus.PENDING.value,
        ),
    )
    csv_data: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    created_count: int = Field(default=0)
    updated_count: int = Field(default=0)
    error_count: int = Field(default=0)
    error_details: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        default=None,
    )
    completed_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True)),
        default=None,
    )
