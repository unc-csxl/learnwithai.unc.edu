import sys

import learnwithai.tables  # noqa: F401
from learnwithai.config import Settings
from learnwithai.db import create_db_and_tables

settings = Settings()

if settings.environment != "development":
    print("This script can only be run in development.", file=sys.stderr)
    print("Add ENVIRONMENT=development to your .env file.", file=sys.stderr)
    exit(1)


create_db_and_tables()
print("Created Database and Tables")
