from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from learnwithai.repositories.course_repository import CourseRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.services.course_service import AuthorizationError, CourseService
from learnwithai.tables.course import Course
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
    return User.model_construct(
        _fields_set=None, pid=pid, name="Test User", onyen="testuser"
    )


def _make_course(course_id: int = 1) -> Course:
    return Course.model_construct(
        _fields_set=None,
        id=course_id,
        name="Intro to CS",
        term="Fall 2026",
        section="001",
    )


def _make_membership(
    user_pid: int = 123456789,
    course_id: int = 1,
    type: MembershipType = MembershipType.STUDENT,
    state: MembershipState = MembershipState.ENROLLED,
) -> Membership:
    mock = MagicMock(spec=Membership)
    mock.user_pid = user_pid
    mock.course_id = course_id
    mock.type = type
    mock.state = state
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
    result = svc.create_course(subject, "Intro to CS", "Fall 2026", "001")

    # Assert
    assert result is course
    course_repo.create.assert_called_once()
    membership_repo.create.assert_called_once()
    created_membership = membership_repo.create.call_args.args[0]
    assert created_membership.user_pid == subject.pid
    assert created_membership.type == MembershipType.INSTRUCTOR
    assert created_membership.state == MembershipState.ENROLLED


# --- get_my_courses ---


def test_get_my_courses_returns_courses_for_active_memberships() -> None:
    # Arrange
    course_repo = MagicMock(spec=CourseRepository)
    membership_repo = MagicMock(spec=MembershipRepository)
    m1 = _make_membership(course_id=1)
    m2 = _make_membership(course_id=2)
    membership_repo.get_active_by_user.return_value = [m1, m2]
    c1 = _make_course(1)
    c2 = _make_course(2)
    course_repo.get_by_id.side_effect = lambda cid: {1: c1, 2: c2}.get(cid)
    svc = _build_service(course_repo, membership_repo)
    subject = _make_user()

    # Act
    result = svc.get_my_courses(subject)

    # Assert
    assert result == [c1, c2]
    membership_repo.get_active_by_user.assert_called_once_with(subject)


def test_get_my_courses_returns_empty_list_when_no_memberships() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_active_by_user.return_value = []
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.get_my_courses(_make_user())

    # Assert
    assert result == []


def test_get_my_courses_skips_missing_courses() -> None:
    # Arrange
    course_repo = MagicMock(spec=CourseRepository)
    membership_repo = MagicMock(spec=MembershipRepository)
    m1 = _make_membership(course_id=1)
    membership_repo.get_active_by_user.return_value = [m1]
    course_repo.get_by_id.return_value = None
    svc = _build_service(course_repo, membership_repo)

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
    membership_repo.get_by_user_and_course.return_value = instructor_m
    membership_repo.get_all_by_course.return_value = roster
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.get_course_roster(user, course)

    # Assert
    assert result == roster
    membership_repo.get_by_user_and_course.assert_called_once_with(user, course)
    membership_repo.get_all_by_course.assert_called_once_with(course)


def test_get_course_roster_returns_roster_for_ta() -> None:
    # Arrange
    membership_repo = MagicMock(spec=MembershipRepository)
    user = _make_user()
    ta_m = _make_membership(user_pid=user.pid, type=MembershipType.TA)
    course = _make_course()
    roster = [ta_m]
    membership_repo.get_by_user_and_course.return_value = ta_m
    membership_repo.get_all_by_course.return_value = roster
    svc = _build_service(membership_repo=membership_repo)

    # Act
    result = svc.get_course_roster(user, course)

    # Assert
    assert result == roster


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
    membership_repo.get_by_user_and_course.assert_called_once_with(
        requesting_user, course
    )
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
    draft_course = Course(name="Draft", term="Fall 2026", section="001")
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
