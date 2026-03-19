"""Seed data for local development and end-to-end tests.

This module exposes a single :func:`seed` function that inserts a fixed set of
users, a course, and memberships into an open database session.
"""

from sqlmodel import Session

from .tables.course import Course
from .tables.membership import Membership, MembershipState, MembershipType
from .tables.user import User


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

    course = Course(name="COMP423", term="Spring 2026", section="001")
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
