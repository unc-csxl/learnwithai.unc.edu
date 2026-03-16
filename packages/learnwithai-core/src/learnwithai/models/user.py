from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, func
from datetime import datetime
import uuid


class User(SQLModel, table=True):
    id: uuid.UUID = Field(
        primary_key=True,
        default_factory=uuid.uuid4,
    )
    name: str
    oauth_tokens: list["OAuthToken"] = Relationship(back_populates="user")
    jwt_tokens: list["UserJwtToken"] = Relationship(back_populates="user")


class UserJwtToken(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: uuid.UUID = Field(foreign_key=f"{User.__tablename__}.id")
    user: User = Relationship(back_populates="jwt_tokens")
    expire_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        )
    )


class OAuthToken(SQLModel, table=True):
    id: uuid.UUID = Field(
        primary_key=True,
        default_factory=uuid.uuid4,
    )
    external_id: str
    family_name: str | None = Field(default=None)
    given_name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    picture: str | None = Field(default=None)
    type: str
    access_token: str
    refresh_token: str
    expiry_time: datetime
    user_id: uuid.UUID = Field(foreign_key=f"{User.__tablename__}.id")
    user: User = Relationship(back_populates="oauth_tokens")
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )
    )
