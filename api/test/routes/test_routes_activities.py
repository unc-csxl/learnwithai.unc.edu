"""Tests for activity route handlers."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from learnwithai.tables.async_job import AsyncJobStatus
from learnwithai.tables.membership import MembershipType

from api.models import (
    ActivityResponse,
    IyowActivityResponse,
    IyowSubmissionResponse,
)
from api.routes.activities import (
    _build_submission_response,
    create_iyow_activity,
    delete_activity,
    get_active_submission,
    get_activity,
    get_student_submission_history,
    list_activities,
    list_submissions,
    submit_iyow_response,
    update_iyow_activity,
)

# ---- helpers ----


def _stub_user(pid: int = 123456789) -> MagicMock:
    mock = MagicMock()
    mock.pid = pid
    return mock


def _stub_course(course_id: int = 1) -> MagicMock:
    mock = MagicMock()
    mock.id = course_id
    return mock


def _stub_activity(
    activity_id: int = 10,
    course_id: int = 1,
    type: str = "iyow",
) -> MagicMock:
    mock = MagicMock()
    mock.id = activity_id
    mock.course_id = course_id
    mock.type = type
    mock.title = "Test Activity"
    mock.release_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock.due_date = datetime(2025, 6, 1, tzinfo=timezone.utc)
    mock.late_date = None
    mock.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return mock


def _stub_iyow_detail(prompt: str = "Explain X", rubric: str = "Rubric") -> MagicMock:
    mock = MagicMock()
    mock.prompt = prompt
    mock.rubric = rubric
    return mock


def _stub_submission(
    submission_id: int = 100,
    activity_id: int = 10,
    student_pid: int = 123456789,
) -> MagicMock:
    mock = MagicMock()
    mock.id = submission_id
    mock.activity_id = activity_id
    mock.student_pid = student_pid
    mock.is_active = True
    mock.submitted_at = datetime(2025, 3, 1, tzinfo=timezone.utc)
    return mock


def _stub_iyow_submission(
    response_text: str = "My response",
    feedback: str | None = None,
    async_job: MagicMock | None = None,
) -> MagicMock:
    mock = MagicMock()
    mock.response_text = response_text
    mock.feedback = feedback
    mock.async_job = async_job
    return mock


def _stub_membership(type: MembershipType = MembershipType.INSTRUCTOR) -> MagicMock:
    mock = MagicMock()
    mock.type = type
    return mock


# ---- list_activities ----


def test_list_activities_returns_list() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity_svc = MagicMock()
    activity_svc.list_activities.return_value = [_stub_activity(), _stub_activity(activity_id=11)]
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = _stub_membership(MembershipType.INSTRUCTOR)
    submission_repo = MagicMock()
    submission_repo.count_active_by_activity.return_value = 3

    result = list_activities(subject, course, activity_svc, membership_repo, submission_repo)

    assert len(result) == 2
    assert all(isinstance(r, ActivityResponse) for r in result)
    assert result[0].active_submission_count == 3


def test_list_activities_student_no_count() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity_svc = MagicMock()
    activity_svc.list_activities.return_value = [_stub_activity()]
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = _stub_membership(MembershipType.STUDENT)
    submission_repo = MagicMock()

    result = list_activities(subject, course, activity_svc, membership_repo, submission_repo)

    assert len(result) == 1
    assert result[0].active_submission_count is None
    submission_repo.count_active_by_activity.assert_not_called()


def test_list_activities_returns_empty_list() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity_svc = MagicMock()
    activity_svc.list_activities.return_value = []
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = _stub_membership(MembershipType.INSTRUCTOR)
    submission_repo = MagicMock()

    result = list_activities(subject, course, activity_svc, membership_repo, submission_repo)

    assert result == []


# ---- create_iyow_activity ----


def test_create_iyow_activity_returns_created_response() -> None:
    subject = _stub_user()
    course = _stub_course()
    iyow_svc = MagicMock()
    activity = _stub_activity()
    detail = _stub_iyow_detail()
    iyow_svc.create_iyow_activity.return_value = (activity, detail)

    body = MagicMock()
    body.title = "Title"
    body.prompt = "Prompt"
    body.rubric = "Rubric"
    body.release_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    body.due_date = datetime(2025, 6, 1, tzinfo=timezone.utc)
    body.late_date = None

    result = create_iyow_activity(subject, course, body, iyow_svc)

    assert isinstance(result, IyowActivityResponse)
    assert result.prompt == "Explain X"
    assert result.rubric == "Rubric"


# ---- get_activity ----


def test_get_activity_staff_sees_rubric() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    activity_svc = MagicMock()
    activity_svc.get_activity.return_value = activity
    iyow_svc = MagicMock()
    detail = _stub_iyow_detail()
    iyow_svc.get_iyow_detail.return_value = detail
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = _stub_membership(MembershipType.INSTRUCTOR)

    result = get_activity(subject, course, activity, activity_svc, iyow_svc, membership_repo)

    assert isinstance(result, IyowActivityResponse)
    assert result.rubric == "Rubric"


def test_get_activity_student_sees_no_rubric() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    activity_svc = MagicMock()
    activity_svc.get_activity.return_value = activity
    iyow_svc = MagicMock()
    detail = _stub_iyow_detail()
    iyow_svc.get_iyow_detail.return_value = detail
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = _stub_membership(MembershipType.STUDENT)

    result = get_activity(subject, course, activity, activity_svc, iyow_svc, membership_repo)

    assert isinstance(result, IyowActivityResponse)
    assert result.rubric is None


def test_get_activity_none_membership_keeps_rubric() -> None:
    """When membership lookup returns None, rubric is not hidden."""
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    activity_svc = MagicMock()
    activity_svc.get_activity.return_value = activity
    iyow_svc = MagicMock()
    detail = _stub_iyow_detail()
    iyow_svc.get_iyow_detail.return_value = detail
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = None

    result = get_activity(subject, course, activity, activity_svc, iyow_svc, membership_repo)

    assert result.rubric == "Rubric"


# ---- update_iyow_activity ----


def test_update_iyow_activity_returns_updated_response() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_svc = MagicMock()
    updated_activity = _stub_activity()
    updated_detail = _stub_iyow_detail(prompt="New Prompt", rubric="New Rubric")
    iyow_svc.update_iyow_activity.return_value = (updated_activity, updated_detail)

    body = MagicMock()
    body.title = "New Title"
    body.prompt = "New Prompt"
    body.rubric = "New Rubric"
    body.release_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    body.due_date = datetime(2025, 6, 1, tzinfo=timezone.utc)
    body.late_date = None

    result = update_iyow_activity(subject, course, activity, body, iyow_svc)

    assert isinstance(result, IyowActivityResponse)
    assert result.prompt == "New Prompt"


# ---- delete_activity ----


def test_delete_activity_calls_service() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    activity_svc = MagicMock()

    result = delete_activity(subject, course, activity, activity_svc)

    assert result is None
    activity_svc.delete_activity.assert_called_once_with(subject, course, activity)


# ---- submit_iyow_response ----


def test_submit_iyow_response_returns_accepted() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    submission = _stub_submission()
    iyow_detail = _stub_iyow_submission()
    iyow_sub_svc.submit.return_value = (submission, iyow_detail)

    body = MagicMock()
    body.response_text = "My answer"

    result = submit_iyow_response(subject, course, activity, body, iyow_sub_svc)

    assert isinstance(result, IyowSubmissionResponse)
    assert result.response_text == "My response"
    assert result.feedback is None


def test_submit_iyow_response_raises_422_on_value_error() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    iyow_sub_svc.submit.side_effect = ValueError("deadline has passed")

    body = MagicMock()
    body.response_text = "text"

    with pytest.raises(HTTPException) as exc_info:
        submit_iyow_response(subject, course, activity, body, iyow_sub_svc)

    assert exc_info.value.status_code == 422


# ---- list_submissions ----


def test_list_submissions_staff_gets_all() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = _stub_membership(MembershipType.INSTRUCTOR)
    pairs = [(_stub_submission(), _stub_iyow_submission(feedback="Good"))]
    iyow_sub_svc.list_submissions_for_activity.return_value = pairs

    result = list_submissions(subject, course, activity, iyow_sub_svc, membership_repo)

    assert len(result) == 1
    assert result[0].feedback == "Good"
    iyow_sub_svc.list_submissions_for_activity.assert_called_once()


def test_list_submissions_ta_gets_all() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = _stub_membership(MembershipType.TA)
    iyow_sub_svc.list_submissions_for_activity.return_value = []

    list_submissions(subject, course, activity, iyow_sub_svc, membership_repo)

    iyow_sub_svc.list_submissions_for_activity.assert_called_once()


def test_list_submissions_student_gets_own() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = _stub_membership(MembershipType.STUDENT)
    iyow_sub_svc.get_student_submissions.return_value = []

    list_submissions(subject, course, activity, iyow_sub_svc, membership_repo)

    iyow_sub_svc.get_student_submissions.assert_called_once()


def test_list_submissions_raises_403_for_non_member() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        list_submissions(subject, course, activity, iyow_sub_svc, membership_repo)

    assert exc_info.value.status_code == 403


# ---- get_active_submission ----


def test_get_active_submission_returns_response() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    submission = _stub_submission()
    iyow_detail = _stub_iyow_submission(feedback="Nice work")
    iyow_sub_svc.get_active_submission.return_value = (submission, iyow_detail)

    result = get_active_submission(subject, course, activity, iyow_sub_svc)

    assert isinstance(result, IyowSubmissionResponse)
    assert result.feedback == "Nice work"


def test_get_active_submission_returns_none() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    iyow_sub_svc.get_active_submission.return_value = None

    result = get_active_submission(subject, course, activity, iyow_sub_svc)

    assert result is None


# ---- _build_submission_response ----


def test_build_submission_response_includes_job_info() -> None:
    submission = _stub_submission()
    async_job = MagicMock()
    async_job.id = 42
    async_job.status = AsyncJobStatus.COMPLETED
    async_job.completed_at = datetime(2025, 3, 1, tzinfo=timezone.utc)

    result = _build_submission_response(submission, "text", "feedback", async_job)

    assert result.job is not None
    assert result.job.id == 42
    assert result.job.status == AsyncJobStatus.COMPLETED


# ---- get_student_submission_history ----


def test_get_student_submission_history_returns_list() -> None:
    subject = _stub_user()
    course = _stub_course()
    activity = _stub_activity()
    iyow_sub_svc = MagicMock()
    pairs = [
        (_stub_submission(), _stub_iyow_submission(feedback="V2 feedback")),
        (_stub_submission(submission_id=101), _stub_iyow_submission(response_text="Old answer")),
    ]
    iyow_sub_svc.get_student_submission_history.return_value = pairs

    result = get_student_submission_history(subject, course, activity, 111111111, iyow_sub_svc)

    assert len(result) == 2
    assert result[0].feedback == "V2 feedback"
    assert result[1].response_text == "Old answer"
    iyow_sub_svc.get_student_submission_history.assert_called_once()
