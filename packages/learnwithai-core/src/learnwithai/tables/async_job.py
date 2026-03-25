"""Database-backed unified async job tracking."""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy.types import JSON
from sqlmodel import (
    Column,
    DateTime,
    Enum,
    Field,
    ForeignKey,
    Integer,
    SQLModel,
    String,
    Text,
    func,
)


class AsyncJobStatus(str, enum.Enum):
    """Lifecycle state of an asynchronous job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AsyncJob(SQLModel, table=True):
    """Tracks the state and results of any asynchronous background job.

    This is a unified table that replaces per-feature job tables. The
    ``kind`` column discriminates the job type, while ``input_data`` and
    ``output_data`` carry type-specific payloads as JSON.
    """

    __tablename__ = "async_job"  # pyright: ignore[reportAssignmentType]

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id"), nullable=False),
    )
    created_by_pid: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    kind: str = Field(
        sa_column=Column(String(64), nullable=False),
    )
    status: AsyncJobStatus = Field(
        default=AsyncJobStatus.PENDING,
        sa_column=Column(
            Enum(
                AsyncJobStatus,
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
            server_default=AsyncJobStatus.PENDING.value,
        ),
    )
    input_data: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    output_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    error_message: str | None = Field(default=None, sa_column=Column(Text))
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
