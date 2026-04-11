# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for the development seed data module."""

from __future__ import annotations

from unittest.mock import MagicMock

from learnwithai.activities.iyow.tables import IyowActivity, IyowSubmission
from learnwithai.dev_data import seed
from learnwithai.tables.activity import Activity
from learnwithai.tables.async_job import AsyncJob, AsyncJobStatus
from learnwithai.tables.membership import MembershipState, MembershipType
from learnwithai.tables.operator import Operator, OperatorRole
from learnwithai.tables.submission import Submission
from learnwithai.tools.jokes.tables import Joke


def test_seed_creates_three_users_one_course_and_three_memberships() -> None:
    session = MagicMock()

    # Track objects added via add_all to verify their attributes after the call
    added: list[list] = []
    session.add_all.side_effect = lambda objs: added.append(list(objs))

    # Track objects added via add to verify their attributes after the call
    added_single: list = []

    _next_id = 1

    def _track_add(obj: object) -> None:
        nonlocal _next_id
        added_single.append(obj)
        # Simulate the database assigning an auto-increment id on flush
        if hasattr(obj, "id") and getattr(obj, "id") is None:
            obj.id = _next_id  # type: ignore[attr-defined]
            _next_id += 1

    session.add.side_effect = _track_add

    seed(session)

    # add_all called three times: users, operators, memberships
    assert session.add_all.call_count == 3
    # add called: course, joke_job, joke_request, iyow_activity, iyow_detail,
    #             iyow_feedback_job, iyow_submission, iyow_submission_detail
    assert session.add.call_count == 8
    # flush called: users, operators, course, memberships, joke_job, joke_request,
    #               iyow_activity, iyow_detail, iyow_feedback_job, iyow_submission,
    #               iyow_submission_detail
    assert session.flush.call_count == 11

    # Verify users
    users = added[0]
    assert len(users) == 4
    pids = {u.pid for u in users}
    assert pids == {111111111, 222222222, 333333333, 444444444}

    # Verify operators
    operators = added[1]
    assert len(operators) == 2
    assert all(isinstance(op, Operator) for op in operators)
    roles = {op.role for op in operators}
    assert OperatorRole.SUPERADMIN in roles
    assert OperatorRole.ADMIN in roles

    # Verify course
    course = added_single[0]
    assert course.course_number == "COMP423"
    assert course.name == "Foundations of Software Engineering"

    # Verify memberships
    memberships = added[2]
    assert len(memberships) == 3
    types = {m.type for m in memberships}
    assert types == {
        MembershipType.INSTRUCTOR,
        MembershipType.STUDENT,
        MembershipType.TA,
    }
    for m in memberships:
        assert m.state == MembershipState.ENROLLED

    # Verify joke job
    joke_job = added_single[1]
    assert isinstance(joke_job, AsyncJob)
    assert joke_job.kind == "joke_generation"
    assert joke_job.status == AsyncJobStatus.COMPLETED
    assert joke_job.input_data["prompt"] == "Tell me 3 jokes about software engineering"
    assert joke_job.output_data is not None
    assert len(joke_job.output_data["jokes"]) == 3

    # Verify joke request
    joke_request = added_single[2]
    assert isinstance(joke_request, Joke)
    assert joke_request.prompt == "Tell me 3 jokes about software engineering"
    assert len(joke_request.jokes) == 3
    assert joke_request.async_job_id == joke_job.id

    # Verify IYOW activity
    iyow_activity = added_single[3]
    assert isinstance(iyow_activity, Activity)
    assert iyow_activity.title == "Explain Dependency Injection"

    iyow_detail = added_single[4]
    assert isinstance(iyow_detail, IyowActivity)
    assert iyow_detail.activity_id == iyow_activity.id
    assert "dependency injection" in iyow_detail.prompt.lower()

    # Verify IYOW feedback job
    iyow_feedback_job = added_single[5]
    assert isinstance(iyow_feedback_job, AsyncJob)
    assert iyow_feedback_job.kind == "iyow_feedback"

    # Verify IYOW submission
    iyow_submission = added_single[6]
    assert isinstance(iyow_submission, Submission)
    assert iyow_submission.is_active is True

    iyow_sub_detail = added_single[7]
    assert isinstance(iyow_sub_detail, IyowSubmission)
    assert iyow_sub_detail.async_job_id == iyow_feedback_job.id
