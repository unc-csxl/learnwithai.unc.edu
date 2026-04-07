# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Seed data for local development and end-to-end tests.

This module exposes a single :func:`seed` function that inserts a fixed set of
users, a course, and memberships into an open database session.
"""

from datetime import datetime, timezone

from sqlmodel import Session

from .activities.iyow.tables import IyowActivity, IyowSubmission
from .tables.activity import Activity, ActivityType
from .tables.async_job import AsyncJob, AsyncJobStatus
from .tables.course import Course, Term
from .tables.membership import Membership, MembershipState, MembershipType
from .tables.submission import Submission
from .tables.user import User
from .tools.jokes.tables import Joke


def seed(session: Session) -> None:
    """Insert development seed data into the database.

    Creates three users, one course (COMP423), and enrolls each user with the
    appropriate role. The caller is responsible for committing the session.

    Args:
        session: An open database session.
    """
    instructor = User(
        pid=222222222,
        name="Ina Instructor",
        onyen="instructor",
        given_name="Ina",
        family_name="Instructor",
        email="instructor@unc.edu",
    )
    student = User(
        pid=111111111,
        name="Sally Student",
        onyen="student",
        given_name="Sally",
        family_name="Student",
        email="student@unc.edu",
    )
    ta = User(
        pid=333333333,
        name="Tatum TA",
        onyen="ta",
        given_name="Tatum",
        family_name="TA",
        email="ta@unc.edu",
    )
    session.add_all([instructor, student, ta])
    session.flush()

    course = Course(
        course_number="COMP423",
        name="Foundations of Software Engineering",
        term=Term.SPRING,
        year=2026,
    )
    session.add(course)
    session.flush()
    assert course.id is not None

    memberships = [
        Membership(
            user_pid=instructor.pid,
            course_id=course.id,
            type=MembershipType.INSTRUCTOR,
            state=MembershipState.ENROLLED,
        ),
        Membership(
            user_pid=student.pid,
            course_id=course.id,
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        ),
        Membership(
            user_pid=ta.pid,
            course_id=course.id,
            type=MembershipType.TA,
            state=MembershipState.ENROLLED,
        ),
    ]
    session.add_all(memberships)
    session.flush()

    joke_job = AsyncJob(
        course_id=course.id,
        created_by_pid=instructor.pid,
        kind="joke_generation",
        status=AsyncJobStatus.COMPLETED,
        input_data={"prompt": "Tell me 3 jokes about software engineering"},
        output_data={
            "jokes": [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "A QA engineer walks into a bar. Orders 1 beer. Orders 0 beers. Orders -1 beers. Orders a lizard.",
                "There are only 10 types of people who understand binary and those who don't.",
            ]
        },
        created_at=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        completed_at=datetime(2025, 1, 15, 10, 0, 12, tzinfo=timezone.utc),
    )
    session.add(joke_job)
    session.flush()

    joke_request = Joke(
        course_id=course.id,
        created_by_pid=instructor.pid,
        prompt="Tell me 3 jokes about software engineering",
        jokes=[
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "A QA engineer walks into a bar. Orders 1 beer. Orders 0 beers. Orders -1 beers. Orders a lizard.",
            "There are only 10 types of people who understand binary and those who don't.",
        ],
        async_job_id=joke_job.id,
        created_at=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
    )
    session.add(joke_request)
    session.flush()

    # --- IYOW Activity ---
    iyow_activity_base = Activity(
        course_id=course.id,
        created_by_pid=instructor.pid,
        type=ActivityType.IYOW,
        title="Explain Dependency Injection",
        release_date=datetime(2025, 1, 10, 0, 0, tzinfo=timezone.utc),
        due_date=datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    session.add(iyow_activity_base)
    session.flush()
    assert iyow_activity_base.id is not None

    iyow_detail = IyowActivity(
        activity_id=iyow_activity_base.id,
        prompt=(
            "In your own words, explain what dependency injection is and why it is useful in software engineering."
        ),
        rubric=(
            "The student should mention: (1) the concept of passing "
            "dependencies to a component rather than having the "
            "component create them; (2) at least one concrete benefit "
            "such as testability, flexibility, or separation of concerns."
        ),
    )
    session.add(iyow_detail)
    session.flush()

    # Completed student submission with feedback
    iyow_feedback_job = AsyncJob(
        course_id=course.id,
        created_by_pid=student.pid,
        kind="iyow_feedback",
        status=AsyncJobStatus.COMPLETED,
        input_data={},
        output_data={"feedback": "Great explanation!"},
        created_at=datetime(2025, 1, 20, 14, 0, tzinfo=timezone.utc),
        completed_at=datetime(2025, 1, 20, 14, 0, 8, tzinfo=timezone.utc),
    )
    session.add(iyow_feedback_job)
    session.flush()
    assert iyow_feedback_job.id is not None

    iyow_submission_base = Submission(
        activity_id=iyow_activity_base.id,
        student_pid=student.pid,
        is_active=True,
        submitted_at=datetime(2025, 1, 20, 14, 0, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 20, 14, 0, tzinfo=timezone.utc),
    )
    session.add(iyow_submission_base)
    session.flush()
    assert iyow_submission_base.id is not None

    iyow_submission_detail = IyowSubmission(
        submission_id=iyow_submission_base.id,
        response_text=(
            "Dependency injection is when you pass the things a class "
            "needs from the outside instead of creating them inside. "
            "This makes it easier to swap out implementations for "
            "testing or when requirements change."
        ),
        feedback=(
            "Great start! You correctly identified that DI involves "
            "passing dependencies from the outside. You also mentioned "
            "testability and flexibility. To strengthen your answer, "
            "you could mention separation of concerns as a design "
            "principle that DI supports."
        ),
        async_job_id=iyow_feedback_job.id,
    )
    session.add(iyow_submission_detail)
    session.flush()
