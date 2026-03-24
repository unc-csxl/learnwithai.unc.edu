from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.dependency_injection import (
    course_repository_factory,
    course_service_factory,
    get_authenticated_user,
    user_repository_factory,
)
from api.main import app
from api.models import (
    AddMemberRequest,
    CourseMembership,
    CourseResponse,
    CreateCourseRequest,
    MembershipResponse,
    RosterMemberResponse,
    UpdateCourseRequest,
)
from api.routes.courses import (
    add_member,
    create_course,
    drop_member,
    get_course_roster,
    list_my_courses,
    update_course,
)
from learnwithai.errors import AuthorizationError
from learnwithai.pagination import PaginatedResult, PaginationParams
from learnwithai.tables.course import Term
from learnwithai.tables.membership import MembershipState, MembershipType


# ---- helpers ----


def _stub_user(
    *,
    pid: int = 123456789,
    name: str = "Test User",
    onyen: str = "testuser",
) -> MagicMock:
    mock = MagicMock()
    mock.pid = pid
    mock.name = name
    mock.onyen = onyen
    return mock


def _stub_course(
    *,
    id: int = 1,
    course_number: str = "COMP101",
    name: str = "Intro to CS",
    description: str = "",
    term: str = "fall",
    year: int = 2026,
) -> MagicMock:
    mock = MagicMock()
    mock.id = id
    mock.course_number = course_number
    mock.name = name
    mock.description = description
    mock.term = term
    mock.year = year
    return mock


def _stub_membership(
    *,
    user_pid: int = 123456789,
    course_id: int = 1,
    type: MembershipType = MembershipType.STUDENT,
    state: MembershipState = MembershipState.ENROLLED,
    course: MagicMock | None = None,
    given_name: str = "Test",
    family_name: str = "User",
    email: str = "test@example.com",
) -> MagicMock:
    mock = MagicMock()
    mock.user_pid = user_pid
    mock.course_id = course_id
    mock.type = type
    mock.state = state
    mock.course = course
    user = MagicMock()
    user.given_name = given_name
    user.family_name = family_name
    user.email = email
    mock.user = user
    return mock


# ---- create_course ----


def test_create_course_returns_course_response() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    course_svc.create_course.return_value = course
    body = CreateCourseRequest(
        course_number="COMP101", name="Intro to CS", term=Term.FALL, year=2026
    )

    # Act
    result = create_course(subject, body, course_svc)

    # Assert
    assert isinstance(result, CourseResponse)
    assert result.name == "Intro to CS"
    assert result.membership == CourseMembership(
        type=MembershipType.INSTRUCTOR,
        state=MembershipState.ENROLLED,
    )
    course_svc.create_course.assert_called_once_with(
        subject, "COMP101", "Intro to CS", Term.FALL, 2026, ""
    )


# ---- list_my_courses ----


def test_list_my_courses_returns_course_list() -> None:
    # Arrange
    user = _stub_user()
    course_svc = MagicMock()
    course_svc.get_my_courses.return_value = [
        _stub_membership(
            type=MembershipType.STUDENT,
            course=_stub_course(id=1),
        ),
        _stub_membership(
            type=MembershipType.TA,
            state=MembershipState.PENDING,
            course=_stub_course(id=2),
        ),
    ]

    # Act
    result = list_my_courses(user, course_svc)

    # Assert
    assert len(result) == 2
    assert all(isinstance(r, CourseResponse) for r in result)
    assert result[0].membership == CourseMembership(
        type=MembershipType.STUDENT,
        state=MembershipState.ENROLLED,
    )
    assert result[1].membership == CourseMembership(
        type=MembershipType.TA,
        state=MembershipState.PENDING,
    )


def test_list_my_courses_returns_empty_list() -> None:
    # Arrange
    user = _stub_user()
    course_svc = MagicMock()
    course_svc.get_my_courses.return_value = []

    # Act
    result = list_my_courses(user, course_svc)

    # Assert
    assert result == []


# ---- get_course_roster ----


def test_get_course_roster_returns_paginated_roster() -> None:
    # Arrange
    user = _stub_user()
    course = _stub_course()
    roster_membership = _stub_membership(type=MembershipType.INSTRUCTOR)
    course_svc = MagicMock()
    course_svc.get_course_roster.return_value = PaginatedResult(
        items=[roster_membership], total=1, page=1, page_size=25
    )
    pagination = PaginationParams()

    # Act
    result = get_course_roster(user, course, course_svc, pagination, "")

    # Assert
    assert len(result.items) == 1
    assert isinstance(result.items[0], RosterMemberResponse)
    assert result.total == 1
    course_svc.get_course_roster.assert_called_once_with(user, course, pagination, "")


# ---- add_member ----


def test_add_member_returns_membership_response() -> None:
    # Arrange
    user = _stub_user()
    course = _stub_course()
    user_repo = MagicMock()
    target_user = _stub_user(pid=999, name="Target User", onyen="targetuser")
    user_repo.get_by_pid.return_value = target_user
    membership = _stub_membership(state=MembershipState.PENDING)
    course_svc = MagicMock()
    course_svc.add_member.return_value = membership
    body = AddMemberRequest(pid=999, type=MembershipType.STUDENT)

    # Act
    result = add_member(
        user,
        course,
        body,
        course_svc,
        user_repo,
    )

    # Assert
    assert isinstance(result, MembershipResponse)
    assert result.state == MembershipState.PENDING
    user_repo.get_by_pid.assert_called_once_with(999)
    course_svc.add_member.assert_called_once_with(
        user,
        course,
        target_user,
        MembershipType.STUDENT,
    )


def test_add_member_raises_404_when_target_user_is_missing() -> None:
    # Arrange
    course = _stub_course()
    subject = _stub_user()
    course_svc = MagicMock()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = None
    body = AddMemberRequest(pid=999, type=MembershipType.STUDENT)

    # Act / Assert
    with pytest.raises(Exception) as exc_info:
        add_member(subject, course, body, course_svc, user_repo)

    assert exc_info.value.status_code == 404  # type: ignore[union-attr]
    assert exc_info.value.detail == "User not found."  # type: ignore[union-attr]
    user_repo.get_by_pid.assert_called_once_with(999)
    course_svc.add_member.assert_not_called()


# ---- drop_member ----


def test_drop_member_returns_membership_response() -> None:
    # Arrange
    user = _stub_user()
    course = _stub_course()
    target_user = _stub_user(pid=999, name="Target User", onyen="targetuser")
    membership = _stub_membership(state=MembershipState.DROPPED)
    course_svc = MagicMock()
    course_svc.drop_member.return_value = membership

    # Act
    result = drop_member(
        user,
        course,
        target_user,
        course_svc,
    )

    # Assert
    assert isinstance(result, MembershipResponse)
    assert result.state == MembershipState.DROPPED
    course_svc.drop_member.assert_called_once_with(user, course, target_user)


# ---- integration tests via TestClient ----


@pytest.mark.integration
def test_create_course_endpoint(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    course = _stub_course()
    mock_svc = MagicMock()
    mock_svc.create_course.return_value = course
    app.dependency_overrides[course_service_factory] = lambda: mock_svc

    # Act
    response = client.post(
        "/api/courses",
        json={
            "course_number": "COMP101",
            "name": "Intro to CS",
            "term": "fall",
            "year": 2026,
        },
    )

    # Assert
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Intro to CS"
    assert body["membership"] == {"type": "instructor", "state": "enrolled"}


@pytest.mark.integration
def test_list_courses_endpoint(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    mock_svc = MagicMock()
    mock_svc.get_my_courses.return_value = [
        _stub_membership(
            type=MembershipType.STUDENT,
            course=_stub_course(),
        )
    ]
    app.dependency_overrides[course_service_factory] = lambda: mock_svc

    # Act
    response = client.get("/api/courses")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Intro to CS"
    assert body[0]["membership"] == {"type": "student", "state": "enrolled"}


@pytest.mark.integration
def test_get_roster_endpoint(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    course = _stub_course()
    mock_svc = MagicMock()
    mock_svc.get_course_roster.return_value = PaginatedResult(
        items=[_stub_membership(type=MembershipType.INSTRUCTOR)],
        total=1,
        page=1,
        page_size=25,
    )
    app.dependency_overrides[course_service_factory] = lambda: mock_svc
    mock_course_repo = MagicMock()
    mock_course_repo.get_by_id.return_value = course
    app.dependency_overrides[course_repository_factory] = lambda: mock_course_repo

    # Act
    response = client.get("/api/courses/1/roster")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["type"] == "instructor"
    assert body["items"][0]["given_name"] == "Test"


@pytest.mark.integration
def test_get_roster_returns_403_for_student(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    course = _stub_course()
    mock_svc = MagicMock()
    mock_svc.get_course_roster.side_effect = AuthorizationError(
        "Insufficient permissions"
    )
    app.dependency_overrides[course_service_factory] = lambda: mock_svc
    mock_course_repo = MagicMock()
    mock_course_repo.get_by_id.return_value = course
    app.dependency_overrides[course_repository_factory] = lambda: mock_course_repo

    # Act
    response = client.get("/api/courses/1/roster")

    # Assert
    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


@pytest.mark.integration
def test_add_member_endpoint(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    course = _stub_course()
    target_user = _stub_user(pid=999, name="Target User", onyen="targetuser")
    mock_svc = MagicMock()
    mock_svc.add_member.return_value = _stub_membership(
        user_pid=999, state=MembershipState.PENDING
    )
    app.dependency_overrides[course_service_factory] = lambda: mock_svc
    mock_course_repo = MagicMock()
    mock_course_repo.get_by_id.return_value = course
    app.dependency_overrides[course_repository_factory] = lambda: mock_course_repo
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_pid.return_value = target_user
    app.dependency_overrides[user_repository_factory] = lambda: mock_user_repo

    # Act
    response = client.post(
        "/api/courses/1/members",
        json={"pid": 999, "type": "student"},
    )

    # Assert
    assert response.status_code == 201
    body = response.json()
    assert body["user_pid"] == 999
    assert body["state"] == "pending"
    mock_svc.add_member.assert_called_once_with(
        user,
        course,
        target_user,
        MembershipType.STUDENT,
    )


@pytest.mark.integration
def test_drop_member_endpoint(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    course = _stub_course()
    target_user = _stub_user(pid=999, name="Target User", onyen="targetuser")
    target_membership = _stub_membership(user_pid=999, state=MembershipState.DROPPED)
    mock_svc = MagicMock()
    mock_svc.drop_member.return_value = target_membership
    app.dependency_overrides[course_service_factory] = lambda: mock_svc
    mock_course_repo = MagicMock()
    mock_course_repo.get_by_id.return_value = course
    app.dependency_overrides[course_repository_factory] = lambda: mock_course_repo
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_pid.return_value = target_user
    app.dependency_overrides[user_repository_factory] = lambda: mock_user_repo

    # Act
    response = client.delete("/api/courses/1/members/999")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "dropped"
    mock_svc.drop_member.assert_called_once_with(user, course, target_user)


@pytest.mark.integration
def test_get_roster_returns_404_when_course_is_missing(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    mock_course_repo = MagicMock()
    mock_course_repo.get_by_id.return_value = None
    app.dependency_overrides[course_repository_factory] = lambda: mock_course_repo

    # Act
    response = client.get("/api/courses/999/roster")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found."}


@pytest.mark.integration
def test_add_member_returns_404_when_target_user_is_missing(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    mock_course_repo = MagicMock()
    mock_course_repo.get_by_id.return_value = _stub_course()
    app.dependency_overrides[course_repository_factory] = lambda: mock_course_repo
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_pid.return_value = None
    app.dependency_overrides[user_repository_factory] = lambda: mock_user_repo

    # Act
    response = client.post(
        "/api/courses/1/members",
        json={"pid": 999, "type": "student"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found."}


@pytest.mark.integration
def test_courses_returns_401_without_token(client: TestClient) -> None:
    # Arrange (no overrides — HTTPBearer rejects missing credentials)

    # Act
    response = client.get("/api/courses")

    # Assert
    assert response.status_code == 401


# ---- update_course ----


def test_update_course_returns_updated_course() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    updated_course = _stub_course(
        course_number="COMP999",
        name="Advanced CS",
        description="Updated",
        term="spring",
        year=2027,
    )
    course_svc.update_course.return_value = updated_course
    instructor_m = _stub_membership(type=MembershipType.INSTRUCTOR)
    course_svc.authorize_instructor.return_value = instructor_m
    body = UpdateCourseRequest(
        course_number="COMP999",
        name="Advanced CS",
        term=Term.SPRING,
        year=2027,
        description="Updated",
    )

    # Act
    result = update_course(subject, course, body, course_svc)

    # Assert
    assert isinstance(result, CourseResponse)
    assert result.course_number == "COMP999"
    assert result.name == "Advanced CS"
    course_svc.update_course.assert_called_once_with(
        subject, course, "COMP999", "Advanced CS", Term.SPRING, 2027, "Updated"
    )


@pytest.mark.integration
def test_put_course_returns_updated_response(client: TestClient) -> None:
    # Arrange
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    mock_course_repo = MagicMock()
    mock_course_repo.get_by_id.return_value = _stub_course()
    app.dependency_overrides[course_repository_factory] = lambda: mock_course_repo
    mock_course_svc = MagicMock()
    updated = _stub_course(
        course_number="COMP999",
        name="Advanced CS",
        description="Updated",
        term="spring",
        year=2027,
    )
    mock_course_svc.update_course.return_value = updated
    instructor_m = _stub_membership(type=MembershipType.INSTRUCTOR)
    mock_course_svc.authorize_instructor.return_value = instructor_m
    app.dependency_overrides[course_service_factory] = lambda: mock_course_svc

    # Act
    response = client.put(
        "/api/courses/1",
        json={
            "course_number": "COMP999",
            "name": "Advanced CS",
            "term": "spring",
            "year": 2027,
            "description": "Updated",
        },
    )

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["course_number"] == "COMP999"
    assert body["name"] == "Advanced CS"
