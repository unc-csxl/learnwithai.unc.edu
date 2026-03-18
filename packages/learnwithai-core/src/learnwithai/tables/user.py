"""Database-backed user models."""

from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Integer, func


class User(SQLModel, table=True):
    """Represents an authenticated LearnWithAI user."""

    pid: int = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=False),
    )
    name: str = Field()
    onyen: str = Field()
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
