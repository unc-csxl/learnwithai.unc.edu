"""Bootstrap a deployed LearnWithAI database for developer resets.

This script is intended to run inside the deployed app image after the target
database has been recreated. It creates all SQLModel tables and inserts a
single dummy user for developer testing.
"""

import learnwithai.tables  # noqa: F401
from learnwithai.db import create_db_and_tables, get_engine
from learnwithai.tables.user import User
from sqlmodel import Session


def main() -> None:
    """Create tables and insert the default dummy user."""
    create_db_and_tables()

    with Session(get_engine()) as session:
        session.add(
            User(
                name="Demo User",
                pid=999999999,
                onyen="demo",
                family_name="User",
                given_name="Demo",
                email="demo@example.com",
            )
        )
        session.commit()

    print("Created tables and dummy user.")


if __name__ == "__main__":
    main()
