# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for IyowSubmissionService."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from learnwithai.activities.iyow.repository import (
    IyowActivityRepository,
    IyowSubmissionRepository,
)
from learnwithai.activities.iyow.submission_service import IyowSubmissionService
from learnwithai.activities.iyow.tables import IyowSubmission
from learnwithai.errors import AuthorizationError
from learnwithai.interfaces import JobQueue
from learnwithai.repositories.activity_repository import ActivityRepository
from learnwithai.repositories.async_job_repository import AsyncJobRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.repositories.submission_repository import SubmissionRepository
from learnwithai.tables.activity import Activity, ActivityType
from learnwithai.tables.async_job import AsyncJob, AsyncJobStatus
from learnwithai.tables.course import Course
from learnwithai.tables.membership import MembershipType
from learnwithai.tables.submission import Submission
from learnwithai.tables.user import User


def _make_service(
    activity_repo: MagicMock | None = None,
    iyow_activity_repo: MagicMock | None = None,
    submission_repo: MagicMock | None = None,
    iyow_submission_repo: MagicMock | None = None,
    async_job_repo: MagicMock | None = None,
    membership_repo: MagicMock | None = None,
    job_queue: MagicMock | None = None,
) -> IyowSubmissionService:
    return IyowSubmissionService(
        activity_repo=activity_repo or MagicMock(spec=ActivityRepository),
        iyow_activity_repo=iyow_activity_repo or MagicMock(spec=IyowActivityRepository),
        submission_repo=submission_repo or MagicMock(spec=SubmissionRepository),
        iyow_submission_repo=iyow_submission_repo or MagicMock(spec=IyowSubmissionRepository),
        async_job_repo=async_job_repo or MagicMock(spec=AsyncJobRepository),
        membership_repo=membership_repo or MagicMock(spec=MembershipRepository),
        job_queue=job_queue or MagicMock(),
    )


def _make_user(pid: int = 123456789) -> MagicMock:
    m = MagicMock(spec=User)
    m.pid = pid
    return m


def _make_course(course_id: int = 1) -> MagicMock:
    m = MagicMock(spec=Course)
    m.id = course_id
    return m


def _make_membership(type: MembershipType = MembershipType.STUDENT) -> MagicMock:
    m = MagicMock()
    m.type = type
    return m


def _make_activity(
    activity_id: int = 10,
    course_id: int = 1,
    type: ActivityType = ActivityType.IYOW,
    release_date: datetime | None = None,
    due_date: datetime | None = None,
    late_date: datetime | None = None,
) -> MagicMock:
    m = MagicMock(spec=Activity)
    m.id = activity_id
    m.course_id = course_id
    m.type = type
    m.release_date = release_date or datetime(2025, 1, 1, tzinfo=timezone.utc)
    m.due_date = due_date or datetime(2025, 6, 1, tzinfo=timezone.utc)
    m.late_date = late_date
    return m


def _make_submission(submission_id: int = 100, activity_id: int = 10) -> MagicMock:
    m = MagicMock(spec=Submission)
    m.id = submission_id
    m.activity_id = activity_id
    m.is_active = True
    return m


def _make_iyow_submission(submission_id: int = 100) -> MagicMock:
    m = MagicMock(spec=IyowSubmission)
    m.submission_id = submission_id
    m.response_text = "My response"
    m.feedback = None
    m.submission = None
    return m


NOW = datetime(2025, 3, 1, tzinfo=timezone.utc)


# ---- submit ----


def test_submit_succeeds_for_student() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)
    submission_repo = MagicMock(spec=SubmissionRepository)
    base_sub = _make_submission()
    submission_repo.create.return_value = base_sub
    async_job_repo = MagicMock(spec=AsyncJobRepository)
    mock_async_job = MagicMock(spec=AsyncJob)
    mock_async_job.id = 200
    async_job_repo.create.return_value = mock_async_job
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_detail = _make_iyow_submission()
    iyow_sub_repo.create.return_value = iyow_detail
    job_queue = MagicMock()

    svc = _make_service(
        submission_repo=submission_repo,
        iyow_submission_repo=iyow_sub_repo,
        async_job_repo=async_job_repo,
        membership_repo=membership_repo,
        job_queue=job_queue,
    )
    result_sub, result_detail = svc.submit(_make_user(), _make_course(), _make_activity(), "My answer", NOW)

    assert result_sub is base_sub
    assert result_detail is iyow_detail
    submission_repo.deactivate_active.assert_called_once()
    submission_repo.create.assert_called_once()
    async_job_repo.create.assert_called_once()
    iyow_sub_repo.create.assert_called_once()
    job_queue.enqueue.assert_called_once()


def test_submit_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError, match="Not a member"):
        svc.submit(_make_user(), _make_course(), _make_activity(), "text", NOW)


def test_submit_succeeds_for_instructor() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)

    submission_repo = MagicMock(spec=SubmissionRepository)
    submission_repo.create.return_value = Submission(
        id=1, activity_id=1, student_pid=222, is_active=True, submitted_at=NOW
    )

    async_job_repo = MagicMock(spec=AsyncJobRepository)
    async_job_repo.create.return_value = AsyncJob(
        id=1, course_id=1, created_by_pid=222, kind="iyow_feedback", status=AsyncJobStatus.PENDING, input_data={}
    )

    iyow_submission_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_submission_repo.create.return_value = IyowSubmission(id=1, submission_id=1, response_text="test text")

    job_queue = MagicMock(spec=JobQueue)

    svc = _make_service(
        membership_repo=membership_repo,
        submission_repo=submission_repo,
        async_job_repo=async_job_repo,
        iyow_submission_repo=iyow_submission_repo,
        job_queue=job_queue,
    )

    sub, iyow_detail = svc.submit(_make_user(), _make_course(), _make_activity(), "test text", NOW)
    assert sub is not None
    assert iyow_detail is not None
    job_queue.enqueue.assert_called_once()


def test_submit_raises_for_wrong_activity_type() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)
    activity = _make_activity()
    activity.type = "other"

    with pytest.raises(ValueError, match="not an IYOW activity"):
        svc.submit(_make_user(), _make_course(), activity, "text", NOW)


def test_submit_raises_when_not_released() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)
    activity = _make_activity(release_date=datetime(2030, 1, 1, tzinfo=timezone.utc))

    with pytest.raises(ValueError, match="not yet released"):
        svc.submit(_make_user(), _make_course(), activity, "text", NOW)


def test_submit_raises_past_due_date() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)
    activity = _make_activity(due_date=datetime(2025, 1, 1, tzinfo=timezone.utc))

    with pytest.raises(ValueError, match="deadline has passed"):
        svc.submit(_make_user(), _make_course(), activity, "text", NOW)


def test_submit_uses_late_date_as_cutoff() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)
    submission_repo = MagicMock(spec=SubmissionRepository)
    submission_repo.create.return_value = _make_submission()
    async_job_repo = MagicMock(spec=AsyncJobRepository)
    mock_async_job = MagicMock(spec=AsyncJob)
    mock_async_job.id = 200
    async_job_repo.create.return_value = mock_async_job
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_sub_repo.create.return_value = _make_iyow_submission()

    svc = _make_service(
        submission_repo=submission_repo,
        iyow_submission_repo=iyow_sub_repo,
        async_job_repo=async_job_repo,
        membership_repo=membership_repo,
    )
    # Due date is past, but late_date is still in the future
    activity = _make_activity(
        due_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        late_date=datetime(2025, 12, 1, tzinfo=timezone.utc),
    )
    svc.submit(_make_user(), _make_course(), activity, "text", NOW)

    submission_repo.create.assert_called_once()


def test_submit_raises_past_late_date() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)
    activity = _make_activity(
        due_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        late_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError, match="deadline has passed"):
        svc.submit(_make_user(), _make_course(), activity, "text", NOW)


# ---- get_active_submission ----


def test_get_active_submission_returns_pair() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership()
    submission_repo = MagicMock(spec=SubmissionRepository)
    base_sub = _make_submission()
    submission_repo.get_active_for_student.return_value = base_sub
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_detail = _make_iyow_submission()
    iyow_sub_repo.get_by_submission_id.return_value = iyow_detail

    svc = _make_service(
        submission_repo=submission_repo,
        iyow_submission_repo=iyow_sub_repo,
        membership_repo=membership_repo,
    )
    result = svc.get_active_submission(_make_user(), _make_course(), _make_activity())

    assert result is not None
    assert result[0] is base_sub
    assert result[1] is iyow_detail


def test_get_active_submission_returns_none_when_no_submission() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership()
    submission_repo = MagicMock(spec=SubmissionRepository)
    submission_repo.get_active_for_student.return_value = None

    svc = _make_service(submission_repo=submission_repo, membership_repo=membership_repo)
    result = svc.get_active_submission(_make_user(), _make_course(), _make_activity())

    assert result is None


def test_get_active_submission_returns_none_when_no_iyow_detail() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership()
    submission_repo = MagicMock(spec=SubmissionRepository)
    submission_repo.get_active_for_student.return_value = _make_submission()
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_sub_repo.get_by_submission_id.return_value = None

    svc = _make_service(
        submission_repo=submission_repo,
        iyow_submission_repo=iyow_sub_repo,
        membership_repo=membership_repo,
    )
    result = svc.get_active_submission(_make_user(), _make_course(), _make_activity())

    assert result is None


def test_get_active_submission_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError, match="Not a member"):
        svc.get_active_submission(_make_user(), _make_course(), _make_activity())


# ---- get_student_submissions ----


def test_get_student_submissions_returns_list() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership()
    submission_repo = MagicMock(spec=SubmissionRepository)
    sub1 = _make_submission(submission_id=100)
    sub2 = _make_submission(submission_id=101)
    submission_repo.list_by_student_and_activity.return_value = [sub1, sub2]
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    detail1 = _make_iyow_submission(100)
    detail2 = _make_iyow_submission(101)
    iyow_sub_repo.get_by_submission_id.side_effect = [detail1, detail2]

    svc = _make_service(
        submission_repo=submission_repo,
        iyow_submission_repo=iyow_sub_repo,
        membership_repo=membership_repo,
    )
    result = svc.get_student_submissions(_make_user(), _make_course(), _make_activity())

    assert len(result) == 2


def test_get_student_submissions_skips_missing_iyow_details() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership()
    submission_repo = MagicMock(spec=SubmissionRepository)
    sub1 = _make_submission(submission_id=100)
    submission_repo.list_by_student_and_activity.return_value = [sub1]
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_sub_repo.get_by_submission_id.return_value = None

    svc = _make_service(
        submission_repo=submission_repo,
        iyow_submission_repo=iyow_sub_repo,
        membership_repo=membership_repo,
    )
    result = svc.get_student_submissions(_make_user(), _make_course(), _make_activity())

    assert len(result) == 0


def test_get_student_submissions_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.get_student_submissions(_make_user(), _make_course(), _make_activity())


# ---- list_submissions_for_activity ----


def test_list_submissions_for_activity_succeeds_for_staff() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    sub = _make_submission()
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    detail = _make_iyow_submission()
    detail.submission = sub
    iyow_sub_repo.list_active_for_activity.return_value = [detail]

    svc = _make_service(
        iyow_submission_repo=iyow_sub_repo,
        membership_repo=membership_repo,
    )
    result = svc.list_submissions_for_activity(_make_user(), _make_course(), _make_activity())

    assert len(result) == 1
    assert result[0] == (sub, detail)
    iyow_sub_repo.list_active_for_activity.assert_called_once_with(10)


def test_list_submissions_for_activity_skips_missing_iyow() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.TA)
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_sub_repo.list_active_for_activity.return_value = []

    svc = _make_service(
        iyow_submission_repo=iyow_sub_repo,
        membership_repo=membership_repo,
    )
    result = svc.list_submissions_for_activity(_make_user(), _make_course(), _make_activity())

    assert len(result) == 0


def test_list_submissions_for_activity_raises_for_student() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.list_submissions_for_activity(_make_user(), _make_course(), _make_activity())


# --- get_student_history ---


def test_get_student_history_returns_tuples_for_instructor() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    submission_repo = MagicMock(spec=SubmissionRepository)
    base_sub = _make_submission()
    submission_repo.list_by_student_and_activity.return_value = [base_sub]
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_detail = MagicMock(spec=IyowSubmission)
    iyow_sub_repo.get_by_submission_id.return_value = iyow_detail

    svc = _make_service(
        submission_repo=submission_repo,
        iyow_submission_repo=iyow_sub_repo,
        membership_repo=membership_repo,
    )
    result = svc.get_student_submission_history(_make_user(), _make_course(), _make_activity(), student_pid=111111111)

    assert len(result) == 1
    assert result[0] == (base_sub, iyow_detail)


def test_get_student_history_skips_missing_iyow_detail() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.TA)
    submission_repo = MagicMock(spec=SubmissionRepository)
    submission_repo.list_by_student_and_activity.return_value = [_make_submission()]
    iyow_sub_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_sub_repo.get_by_submission_id.return_value = None

    svc = _make_service(
        submission_repo=submission_repo,
        iyow_submission_repo=iyow_sub_repo,
        membership_repo=membership_repo,
    )
    result = svc.get_student_submission_history(_make_user(), _make_course(), _make_activity(), student_pid=111111111)

    assert len(result) == 0


def test_get_student_history_raises_for_student() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.get_student_submission_history(_make_user(), _make_course(), _make_activity(), student_pid=111111111)


def test_list_submissions_for_activity_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.list_submissions_for_activity(_make_user(), _make_course(), _make_activity())


def test_list_submissions_with_roster_includes_non_submitters() -> None:
    from learnwithai.tables.membership import Membership, MembershipState

    student_a = User(pid=111, name="Alice A", onyen="aa", given_name="Alice", family_name="A")
    student_b = User(pid=222, name="Bob B", onyen="bb", given_name="Bob", family_name="B")
    mem_a = Membership(user_pid=111, course_id=1, type=MembershipType.STUDENT, state=MembershipState.ENROLLED)
    mem_a.user = student_a  # type: ignore[assignment]
    mem_b = Membership(user_pid=222, course_id=1, type=MembershipType.STUDENT, state=MembershipState.ENROLLED)
    mem_b.user = student_b  # type: ignore[assignment]

    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    membership_repo.get_enrolled_students.return_value = [mem_a, mem_b]

    # Only student_a submitted
    sub = Submission(id=10, activity_id=1, student_pid=111, is_active=True, submitted_at=NOW)
    iyow_sub = IyowSubmission(id=10, submission_id=10, response_text="answer")
    iyow_sub.submission = sub
    iyow_submission_repo = MagicMock(spec=IyowSubmissionRepository)
    iyow_submission_repo.list_active_for_activity.return_value = [iyow_sub]

    svc = _make_service(
        membership_repo=membership_repo,
        iyow_submission_repo=iyow_submission_repo,
    )

    result = svc.list_submissions_with_roster(_make_user(), _make_course(), _make_activity())

    assert len(result) == 2
    # Sorted by family name: "A" before "B"
    assert result[0][0].pid == 111
    assert result[0][1] is not None
    assert result[0][2] is not None
    assert result[1][0].pid == 222
    assert result[1][1] is None
    assert result[1][2] is None
    iyow_submission_repo.list_active_for_activity.assert_called_once_with(10)
    iyow_submission_repo.get_by_submission_id.assert_not_called()


def test_list_submissions_with_roster_raises_for_student() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.list_submissions_with_roster(_make_user(), _make_course(), _make_activity())
