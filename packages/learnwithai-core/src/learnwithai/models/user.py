"""Database-backed user models."""

from datetime import datetime
import uuid

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, func


class User(SQLModel, table=True):
    """Represents an authenticated LearnWithAI user."""

    id: uuid.UUID = Field(
        primary_key=True,
        default_factory=uuid.uuid4,
    )
    name: str
    pid: str
    onyen: str
    family_name: str | None = Field(default=None)
    given_name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        default=None,
    )
