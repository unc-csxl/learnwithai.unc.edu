from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import TEXT, Column, DateTime, func, JSON, Float
from sqlalchemy.dialects.postgresql import ARRAY
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import uuid

class User(SQLModel, table=True):
    id: uuid.UUID = Field(
        primary_key=True,
        default_factory=uuid.uuid4,
    )
    name: str
    oauth_tokens: list["OAuthToken"] = Relationship(back_populates="user")
    jwt_tokens: list["UserJwtToken"] = Relationship(back_populates="user")