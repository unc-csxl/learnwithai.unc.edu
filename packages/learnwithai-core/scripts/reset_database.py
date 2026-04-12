# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Reset the development database and seed it with sample data.

This script is idempotent:

* **First run** (before any tables exist): creates all tables and seeds data.
* **Subsequent runs**: drops and recreates the database, then creates tables
  and seeds data.
"""

import sys

import learnwithai.tables  # noqa: F401
from learnwithai.config import Settings
from learnwithai.db import create_db_and_tables, get_engine, reset_db_and_tables
from learnwithai.dev_data import seed
from sqlalchemy import inspect
from sqlmodel import Session


def main() -> None:
    """Reset the development database and insert seed data."""
    settings = Settings()

    if settings.environment != "development":
        print("This script can only be run in development.", file=sys.stderr)
        print("Add ENVIRONMENT=development to your .env file.", file=sys.stderr)
        raise SystemExit(1)

    if _tables_exist():
        reset_db_and_tables()
    else:
        create_db_and_tables()

    with Session(get_engine()) as session:
        seed(session)
        session.commit()

    print("Reset database and seeded development data.")


def _tables_exist() -> bool:
    """Returns ``True`` when at least one application table is present."""
    inspector = inspect(get_engine())
    return len(inspector.get_table_names()) > 0


if __name__ == "__main__":
    main()
