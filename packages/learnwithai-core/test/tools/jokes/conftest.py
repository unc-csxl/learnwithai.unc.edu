"""Shared fixtures for joke repository integration tests."""

from __future__ import annotations

import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

DEFAULT_TEST_DB_URL = "postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai_test"
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB_URL)


@pytest.fixture()
def session():
    """Provide a transactional session that rolls back after each test."""
    engine = create_engine(TEST_DB_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
        session.rollback()
