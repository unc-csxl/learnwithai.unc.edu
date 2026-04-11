# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Grant operator access to a user in a deployed database.

Usage:
    uv run --package learnwithai-core python -m learnwithai.scripts.grant_operator \
        --pid 123456789 --role superadmin --created-by 123456789

Roles: superadmin, admin, helpdesk.
"""

import argparse

import learnwithai.tables  # noqa: F401 — register all SQLModel tables
from learnwithai.db import get_engine
from learnwithai.tables.operator import Operator, OperatorRole
from sqlmodel import Session


def main() -> None:
    """Parse arguments and insert an Operator record."""
    parser = argparse.ArgumentParser(description="Grant operator access to a user.")
    parser.add_argument("--pid", type=int, required=True, help="PID of the user to promote.")
    parser.add_argument(
        "--role",
        type=str,
        required=True,
        choices=[r.value for r in OperatorRole],
        help="Operator role to assign.",
    )
    parser.add_argument(
        "--created-by",
        type=int,
        required=True,
        help="PID of the user performing the grant.",
    )
    args = parser.parse_args()

    with Session(get_engine()) as session:
        operator = Operator(
            user_pid=args.pid,
            role=OperatorRole(args.role),
            created_by_pid=args.created_by,
        )
        session.add(operator)
        session.commit()

    print(f"Granted {args.role} access to PID {args.pid}.")


if __name__ == "__main__":
    main()
