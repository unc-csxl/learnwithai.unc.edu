# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from learnwithai.errors import AuthorizationError
from learnwithai.pagination import PaginatedResult, PaginationParams
from learnwithai.repositories.course_repository import CourseRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.services.course_service import CourseService
from learnwithai.tables.course import Course, Term
from learnwithai.tables.membership import Membership, MembershipState, MembershipType
from learnwithai.tables.user import User


def _build_service(
    course_repo: CourseRepository | None = None,
    membership_repo: MembershipRepository | None = None,
) -> CourseService:
    if course_repo is None:
        course_repo = MagicMock(spec=CourseRepository)
    if membership_repo is None:
        membership_repo = MagicMock(spec=MembershipRepository)
    return CourseService(course_repo, membership_repo)


def _make_user(pid: int = 123456789) -> User:
    return User.model_construct(_fields_set=None, pid=pid, name="Test User", onyen="testuser")


def _make_course(course_id: int = 1) -> Course:
    return Course.model_construct(
        _fields_set=None,
        id=course_id,
        course_number="COMP101",
        name="Intro to CS",
        description="",
        term=Term.FALL,
        year=2026,
    )


def _make_membership(
    user_pid: int = 123456789,
    course_id: int = 1,
    type: MembershipType = MembershipType.STUDENT,
    state: MembershipState = MembershipState.ENROLLED,
    course: Course | None = None,
) -> Membership:
    mock = MagicMock(spec=Membership)
    mock.user_pid = user_pid
    mock.course_id = course_id
    mock.type = type
    mock.state = state
    mock.course = course
    return mock  # type: ignore[return-value]


# --- create_course ---


def test_create_course_creates_and_enrolls_instructor() -> None:
    # Arrange
    course_repo = MagicMock(spec=CourseRepository)
    membership_repo = MagicMock(spec=MembershipRepository)
    course = _make_course()
    course_repo.create.return_value = course
    svc = _build_service(course_repo, membership_repo)
    subject = _make_user()

    # Act
    result = svc.create_course(subject, "COMP101", "Intro to CS", Term.FALL, 2026)

    # Assert
    assert result is course
    course_repo.create.assert_called_once()
    membership_repo.create.assert_called_once()
    created_membership = membership_repo.create.call_args.args[0]
    assert created_membership.user_pid == subject.pid
    assert created_membership.type == MembershipType.INSTRUCTOR
    assert created_membership.state == MembershipState.ENROLLED


# --- authorize_instructor ---


def test_authorize_instructor_returns_membership_for_instructor() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    instructor = _make_membership(type=MembershipType.INSTRUCTOR)
    membership_repo.get_by_user_and_course.return_value = instructor
    svc = _build_service(membership_repo=membership_repo)
    subject = _make_user()
    course = _make_course()

    # Act
    result = svc.authorize_instructor(subject, course)

    # Assert
    assert result is instructor


def test_authorize_instructor_raises_for_non_instructor() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    student = _make_membership(type=MembershipType.STUDENT)
    membership_repo.get_by_user_and_course.return_value = student
    svc = _build_service(membership_repo=membership_repo)
    subject = _make_user()
    course = _make_course()

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.authorize_instructor(subject, course)


def test_authorize_instructor_raises_for_non_member() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None
    svc = _build_service(membership_repo=membership_repo)
    subject = _make_user()
    course = _make_course()

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.authorize_instructor(subject, course)


# --- get_my_courses ---


def test_get_my_courses_returns_courses_for_active_memberships() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    c1 = _make_course(1)
    c2 = _make_course(2)
    m1 = _make_membership(course_id=1, course=c1)
    m2 = _make_membership(course_id=2, course=c2)
    membership_repo.get_active_by_user.return_value = [m1, m2]
    svc = _build_service(membership_repo=membership_repo)
    subject = _make_user()

    # Act
    result = svc.get_my_courses(subject)

    # Assert
    assert result == [m1, m2]
    membership_repo.get_active_by_user.assert_called_once_with(subject)


def test_get_my_courses_preserves_membership_context() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    course = _make_course(1)
    membership = _make_membership(
        course_id=1,
        type=MembershipType.TA,
        state=MembershipState.PENDING,
        course=course,
    )
    membership_repo.get_active_by_user.return_value = [membership]
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.get_my_courses(_make_user())

    # Assert
    assert result[0] is membership
    assert result[0].course is course


def test_get_my_courses_returns_empty_list_when_no_memberships() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_active_by_user.return_value = []
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.get_my_courses(_make_user())

    # Assert
    assert result == []


# --- get_course_roster ---


def test_get_course_roster_returns_roster_for_instructor() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    user = _make_user()
    instructor_m = _make_membership(type=MembershipType.INSTRUCTOR)
    course = _make_course()
    roster = [instructor_m, _make_membership(user_pid=999)]
    paginated = PaginatedResult[Membership](items=roster, total=2, page=1, page_size=25)
    membership_repo.get_by_user_and_course.return_value = instructor_m
    membership_repo.get_roster_page.return_value = paginated
    svc = _build_service(membership_repo=membership_repo)
    pagination = PaginationParams()

    # Act
    result = svc.get_course_roster(user, course, pagination)

    # Assert
    assert result.items == roster
    assert result.total == 2
    membership_repo.get_by_user_and_course.assert_called_once_with(user, course)
    membership_repo.get_roster_page.assert_called_once_with(course, pagination, "")


def test_get_course_roster_returns_roster_for_ta() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    user = _make_user()
    ta_m = _make_membership(user_pid=user.pid, type=MembershipType.TA)
    course = _make_course()
    paginated = PaginatedResult[Membership](items=[ta_m], total=1, page=1, page_size=25)
    membership_repo.get_by_user_and_course.return_value = ta_m
    membership_repo.get_roster_page.return_value = paginated
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.get_course_roster(user, course)

    # Assert
    assert result.items == [ta_m]


def test_get_course_roster_raises_for_student() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    student_m = _make_membership(type=MembershipType.STUDENT)
    membership_repo.get_by_user_and_course.return_value = student_m
    svc = _build_service(membership_repo=membership_repo)

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.get_course_roster(_make_user(), _make_course())


def test_get_course_roster_raises_for_non_member() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None
    svc = _build_service(membership_repo=membership_repo)

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.get_course_roster(_make_user(), _make_course())


# --- add_member ---


def test_add_member_creates_pending_membership() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    requesting_user = _make_user()
    instructor_m = _make_membership(type=MembershipType.INSTRUCTOR)
    course = _make_course()
    target_user = _make_user(999)
    new_m = _make_membership(user_pid=999, state=MembershipState.PENDING)
    membership_repo.get_by_user_and_course.return_value = instructor_m
    membership_repo.create.return_value = new_m
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.add_member(
        requesting_user,
        course,
        target_user,
        MembershipType.STUDENT,
    )

    # Assert
    assert result is new_m
    membership_repo.get_by_user_and_course.assert_called_once_with(requesting_user, course)
    created = membership_repo.create.call_args.args[0]
    assert created.user_pid == target_user.pid
    assert created.course_id == course.id
    assert created.state == MembershipState.PENDING


def test_add_member_raises_for_non_instructor() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    student_m = _make_membership(type=MembershipType.STUDENT)
    membership_repo.get_by_user_and_course.return_value = student_m
    svc = _build_service(membership_repo=membership_repo)

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.add_member(
            _make_user(),
            _make_course(),
            _make_user(999),
            MembershipType.STUDENT,
        )


def test_add_member_raises_for_unpersisted_course() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    instructor_m = _make_membership(type=MembershipType.INSTRUCTOR)
    draft_course = Course(course_number="COMP999", name="Draft", term=Term.FALL, year=2026)
    membership_repo.get_by_user_and_course.return_value = instructor_m
    svc = _build_service(membership_repo=membership_repo)

    # Act / Assert
    with pytest.raises(ValueError, match="Course must be persisted"):
        svc.add_member(
            _make_user(),
            draft_course,
            _make_user(999),
            MembershipType.STUDENT,
        )


# --- drop_member ---


def test_drop_member_instructor_drops_student() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    requesting_user = _make_user(pid=100)
    instructor_m = _make_membership(user_pid=100, type=MembershipType.INSTRUCTOR)
    target_user = _make_user(pid=200)
    student_m = _make_membership(user_pid=200, type=MembershipType.STUDENT)
    course = _make_course()
    membership_repo.get_by_user_and_course.side_effect = [instructor_m, student_m]
    membership_repo.update.side_effect = lambda membership: membership
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.drop_member(requesting_user, course, target_user)

    # Assert
    assert result.state == MembershipState.DROPPED


def test_drop_member_student_drops_self() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    requesting_user = _make_user(pid=200)
    student_m = _make_membership(user_pid=200, type=MembershipType.STUDENT)
    course = _make_course()
    membership_repo.get_by_user_and_course.side_effect = [student_m, student_m]
    membership_repo.update.side_effect = lambda membership: membership
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.drop_member(requesting_user, course, requesting_user)

    # Assert
    assert result.state == MembershipState.DROPPED


def test_drop_member_student_cannot_drop_other() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    requesting_user = _make_user(pid=200)
    student_m = _make_membership(user_pid=200, type=MembershipType.STUDENT)
    membership_repo.get_by_user_and_course.side_effect = [
        student_m,
        _make_membership(user_pid=300, type=MembershipType.STUDENT),
    ]
    svc = _build_service(membership_repo=membership_repo)

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.drop_member(requesting_user, _make_course(), _make_user(pid=300))


def test_drop_member_raises_when_not_member() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None
    svc = _build_service(membership_repo=membership_repo)

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.drop_member(_make_user(), _make_course(), _make_user(pid=200))


def test_drop_member_raises_when_target_not_found() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    instructor_m = _make_membership(user_pid=100, type=MembershipType.INSTRUCTOR)
    membership_repo.get_by_user_and_course.side_effect = [instructor_m, None]
    svc = _build_service(membership_repo=membership_repo)

    # Act / Assert
    with pytest.raises(ValueError, match="Target membership does not exist"):
        svc.drop_member(_make_user(pid=100), _make_course(), _make_user(pid=200))


# --- update_course ---


def test_update_course_updates_fields() -> None:
    # Arrange
    course_repo = MagicMock(spec=CourseRepository)
    membership_repo = MagicMock(spec=MembershipRepository)
    course = MagicMock(spec=Course)
    course.id = 1
    instructor_m = _make_membership(user_pid=123456789, type=MembershipType.INSTRUCTOR)
    membership_repo.get_by_user_and_course.return_value = instructor_m
    updated_course = _make_course()
    course_repo.update.return_value = updated_course
    svc = _build_service(course_repo, membership_repo)
    subject = _make_user()

    # Act
    result = svc.update_course(subject, course, "COMP999", "New Name", Term.SPRING, 2027, "New desc")

    # Assert
    assert result is updated_course
    course_repo.update.assert_called_once_with(course)


def test_update_course_raises_when_not_instructor() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    student_m = _make_membership(type=MembershipType.STUDENT)
    membership_repo.get_by_user_and_course.return_value = student_m
    svc = _build_service(membership_repo=membership_repo)
    course = MagicMock(spec=Course)

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.update_course(_make_user(), course, "COMP999", "New", Term.FALL, 2027)


def test_update_course_raises_when_not_member() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None
    svc = _build_service(membership_repo=membership_repo)
    course = MagicMock(spec=Course)

    # Act / Assert
    with pytest.raises(AuthorizationError):
        svc.update_course(_make_user(), course, "COMP999", "New", Term.FALL, 2027)
