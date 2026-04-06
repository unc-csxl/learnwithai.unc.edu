"""Tests for IyowFeedbackJobHandler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from learnwithai.activities.iyow.job import IyowFeedbackJobHandler
from learnwithai.activities.iyow.models import IyowFeedbackJob


def test_iyow_feedback_job_type() -> None:
    job = IyowFeedbackJob(job_id=1)
    assert job.type == "iyow_feedback"


def test_handler_generates_feedback_and_stores_result() -> None:
    job_payload = IyowFeedbackJob(job_id=42)
    handler = IyowFeedbackJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()

    # Mock async job
    mock_async_job = MagicMock()
    mock_async_job.id = 42
    mock_async_job.course_id = 1
    mock_async_job.created_by_pid = 222222222
    mock_async_job.kind = "iyow_feedback"
    mock_async_job.status = MagicMock(value="completed")

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    # Mock IYOW submission
    mock_iyow_submission = MagicMock()
    mock_iyow_submission.submission_id = 100
    mock_iyow_submission.response_text = "My explanation of concept X"
    mock_iyow_submission.feedback = None

    mock_iyow_submission_repo_cls = MagicMock()
    mock_iyow_submission_repo_instance = MagicMock()
    mock_iyow_submission_repo_instance.get_by_async_job_id.return_value = mock_iyow_submission
    mock_iyow_submission_repo_cls.return_value = mock_iyow_submission_repo_instance

    # Mock base submission
    mock_base_submission = MagicMock()
    mock_base_submission.id = 100
    mock_base_submission.activity_id = 10

    mock_submission_repo_cls = MagicMock()
    mock_submission_repo_instance = MagicMock()
    mock_submission_repo_instance.get_by_id.return_value = mock_base_submission
    mock_submission_repo_cls.return_value = mock_submission_repo_instance

    # Mock IYOW activity
    mock_iyow_activity = MagicMock()
    mock_iyow_activity.rubric = "Good answer mentions A, B, C"

    mock_iyow_activity_repo_cls = MagicMock()
    mock_iyow_activity_repo_instance = MagicMock()
    mock_iyow_activity_repo_instance.get_by_activity_id.return_value = mock_iyow_activity
    mock_iyow_activity_repo_cls.return_value = mock_iyow_activity_repo_instance

    # Mock AI service
    mock_ai_svc = MagicMock()
    mock_ai_svc.complete.return_value = "Great job! You mentioned A and B well."

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-4o-mini"

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.IyowSubmissionRepository",
            mock_iyow_submission_repo_cls,
        ),
        patch(
            "learnwithai.repositories.submission_repository.SubmissionRepository",
            mock_submission_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.IyowActivityRepository",
            mock_iyow_activity_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "learnwithai.activities.iyow.job.AiCompletionService",
            return_value=mock_ai_svc,
        ),
    ):
        handler.handle(job_payload)

    mock_ai_svc.complete.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()
    assert mock_iyow_submission.feedback == "Great job! You mentioned A and B well."
    assert mock_async_job.output_data == {"feedback": "Great job! You mentioned A and B well."}


def test_handler_raises_when_api_key_not_set() -> None:
    job_payload = IyowFeedbackJob(job_id=42)
    handler = IyowFeedbackJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()
    mock_async_job = MagicMock()
    mock_async_job.course_id = 1
    mock_async_job.created_by_pid = 222222222
    mock_async_job.kind = "iyow_feedback"
    mock_async_job.status = MagicMock(value="failed")

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_settings = MagicMock()
    mock_settings.openai_api_key = None

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(RuntimeError, match="openai_api_key is not configured"),
    ):
        handler.handle(job_payload)

    mock_session.rollback.assert_called_once()


def test_handler_raises_when_async_job_not_found() -> None:
    job_payload = IyowFeedbackJob(job_id=42)
    handler = IyowFeedbackJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = None
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-4o-mini"

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(ValueError, match="AsyncJob 42 not found"),
    ):
        handler.handle(job_payload)


def test_handler_raises_when_iyow_submission_not_found() -> None:
    job_payload = IyowFeedbackJob(job_id=42)
    handler = IyowFeedbackJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()

    mock_async_job = MagicMock()
    mock_async_job.id = 42

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_iyow_sub_repo_cls = MagicMock()
    mock_iyow_sub_repo_instance = MagicMock()
    mock_iyow_sub_repo_instance.get_by_async_job_id.return_value = None
    mock_iyow_sub_repo_cls.return_value = mock_iyow_sub_repo_instance

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-4o-mini"

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.IyowSubmissionRepository",
            mock_iyow_sub_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(ValueError, match="IyowSubmission for AsyncJob 42 not found"),
    ):
        handler.handle(job_payload)


def test_handler_raises_when_base_submission_not_found() -> None:
    job_payload = IyowFeedbackJob(job_id=42)
    handler = IyowFeedbackJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()

    mock_async_job = MagicMock()
    mock_async_job.id = 42

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_iyow_submission = MagicMock()
    mock_iyow_submission.submission_id = 100

    mock_iyow_sub_repo_cls = MagicMock()
    mock_iyow_sub_repo_instance = MagicMock()
    mock_iyow_sub_repo_instance.get_by_async_job_id.return_value = mock_iyow_submission
    mock_iyow_sub_repo_cls.return_value = mock_iyow_sub_repo_instance

    mock_submission_repo_cls = MagicMock()
    mock_submission_repo_instance = MagicMock()
    mock_submission_repo_instance.get_by_id.return_value = None
    mock_submission_repo_cls.return_value = mock_submission_repo_instance

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-4o-mini"

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.IyowSubmissionRepository",
            mock_iyow_sub_repo_cls,
        ),
        patch(
            "learnwithai.repositories.submission_repository.SubmissionRepository",
            mock_submission_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(ValueError, match="Submission 100 not found"),
    ):
        handler.handle(job_payload)


def test_handler_raises_when_iyow_activity_not_found() -> None:
    job_payload = IyowFeedbackJob(job_id=42)
    handler = IyowFeedbackJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()

    mock_async_job = MagicMock()
    mock_async_job.id = 42

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_iyow_submission = MagicMock()
    mock_iyow_submission.submission_id = 100

    mock_iyow_sub_repo_cls = MagicMock()
    mock_iyow_sub_repo_instance = MagicMock()
    mock_iyow_sub_repo_instance.get_by_async_job_id.return_value = mock_iyow_submission
    mock_iyow_sub_repo_cls.return_value = mock_iyow_sub_repo_instance

    mock_base_submission = MagicMock()
    mock_base_submission.id = 100
    mock_base_submission.activity_id = 10

    mock_submission_repo_cls = MagicMock()
    mock_submission_repo_instance = MagicMock()
    mock_submission_repo_instance.get_by_id.return_value = mock_base_submission
    mock_submission_repo_cls.return_value = mock_submission_repo_instance

    mock_iyow_activity_repo_cls = MagicMock()
    mock_iyow_activity_repo_instance = MagicMock()
    mock_iyow_activity_repo_instance.get_by_activity_id.return_value = None
    mock_iyow_activity_repo_cls.return_value = mock_iyow_activity_repo_instance

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-4o-mini"

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.IyowSubmissionRepository",
            mock_iyow_sub_repo_cls,
        ),
        patch(
            "learnwithai.repositories.submission_repository.SubmissionRepository",
            mock_submission_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.IyowActivityRepository",
            mock_iyow_activity_repo_cls,
        ),
        patch(
            "learnwithai.activities.iyow.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(ValueError, match="IyowActivity for activity 10 not found"),
    ):
        handler.handle(job_payload)
