"""Tests for the development seed data module."""

from __future__ import annotations

from unittest.mock import MagicMock

from learnwithai.dev_data import seed
from learnwithai.tables.course import Course
from learnwithai.tables.membership import MembershipState, MembershipType


def test_seed_creates_three_users_one_course_and_three_memberships() -> None:
    session = MagicMock()

    # Track objects added via add_all to verify their attributes after the call
    added: list[list] = []
    session.add_all.side_effect = lambda objs: added.append(list(objs))

    # Track objects added via add to verify their attributes after the call
    added_single: list = []

    def _track_add(obj: object) -> None:
        added_single.append(obj)
        # Simulate the database assigning an auto-increment id on flush
        if isinstance(obj, Course):
            obj.id = 1

    session.add.side_effect = _track_add

    seed(session)

    # add_all called twice: once for users, once for memberships
    assert session.add_all.call_count == 2
    # add called once: for the course
    assert session.add.call_count == 1
    # flush called three times: after users, after course, after memberships
    assert session.flush.call_count == 3

    # Verify users
    users = added[0]
    assert len(users) == 3
    pids = {u.pid for u in users}
    assert pids == {111111111, 222222222, 333333333}

    # Verify course
    course = added_single[0]
    assert course.course_number == "COMP423"
    assert course.name == "Foundations of Software Engineering"

    # Verify memberships
    memberships = added[1]
    assert len(memberships) == 3
    types = {m.type for m in memberships}
    assert types == {
        MembershipType.INSTRUCTOR,
        MembershipType.STUDENT,
        MembershipType.TA,
    }
    for m in memberships:
        assert m.state == MembershipState.ENROLLED
