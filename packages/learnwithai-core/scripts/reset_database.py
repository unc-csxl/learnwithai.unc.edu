"""Drop and recreate the development database, then rebuild all tables."""

import sys

import learnwithai.tables  # noqa: F401
from learnwithai.config import Settings
from learnwithai.db import reset_db_and_tables


def main() -> None:
    """Reset the development database from scratch."""
    settings = Settings()

    if settings.environment != "development":
        print("This script can only be run in development.", file=sys.stderr)
        print("Add ENVIRONMENT=development to your .env file.", file=sys.stderr)
        raise SystemExit(1)

    reset_db_and_tables()
    print("Reset Database and Tables")


if __name__ == "__main__":
    main()
