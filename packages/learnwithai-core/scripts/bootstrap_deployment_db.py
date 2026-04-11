# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Bootstrap a deployed LearnWithAI database for developer resets.

This script is intended to run inside the deployed app image after the target
database has been recreated. It creates all SQLModel tables.
"""

import learnwithai.tables  # noqa: F401
from learnwithai.db import create_db_and_tables


def main() -> None:
    """Create tables and insert the default dummy user with operator access."""
    create_db_and_tables()
    print("Created tables.")


if __name__ == "__main__":
    main()
