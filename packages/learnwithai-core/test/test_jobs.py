from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from learnwithai.jobs import (
    EchoJob,
    ForbiddenJobQueue,
    JokeGenerationJob,
    JobPayload,
    RosterUploadJob,
    get_job_handler_map,
    job_adapter,
    job_payload_adapter,
)
from learnwithai.jobs.echo import EchoJobHandler
from learnwithai.jobs.roster_upload import RosterUploadJobHandler
from pydantic import ValidationError


def test_jobs_package_exports_expected_symbols() -> None:
    # Arrange
    from learnwithai import jobs

    # Act
    exported_names = jobs.__all__

    # Assert
    assert exported_names == [
        "BaseJobHandler",
        "Job",
        "EchoJob",
        "ForbiddenJobQueue",
        "JokeGenerationJob",
        "NoOpJobNotifier",
        "RosterUploadJob",
        "RosterUploadOutput",
        "JobPayload",
        "get_job_handler_map",
    ]


def test_job_payload_alias_is_annotated_union() -> None:
    # Arrange / Act
    import typing

    origin = typing.get_origin(JobPayload)

    # Assert — discriminated unions are wrapped in Annotated
    assert origin is typing.Annotated


def test_job_adapter_builds_echo_job_from_payload() -> None:
    # Arrange
    payload = {"type": "echo", "message": "hello"}

    # Act
    job = job_adapter(payload)

    # Assert
    assert isinstance(job, EchoJob)
    assert job.message == "hello"


def test_job_payload_adapter_builds_echo_job_from_payload() -> None:
    # Arrange
    payload = {"type": "echo", "message": "hello"}

    # Act
    job = job_payload_adapter.validate_python(payload)

    # Assert
    assert isinstance(job, EchoJob)
    assert job.message == "hello"


def test_job_adapter_rejects_unknown_job_type() -> None:
    # Arrange
    payload = {"type": "missing", "message": "hello"}

    # Act

    # Assert
    with pytest.raises(ValidationError):
        job_adapter(payload)


def test_job_handler_map_points_echo_job_to_echo_handler() -> None:
    # Arrange
    handler_class = get_job_handler_map()[EchoJob]

    # Act
    handler = handler_class()

    # Assert
    assert isinstance(handler, EchoJobHandler)


def test_echo_job_handler_prints_payload_with_health_status() -> None:
    # Arrange
    job = EchoJob(message="hello")
    handler = EchoJobHandler()
    expected_status = {"status": "ok"}

    # Act
    with (
        patch("learnwithai.jobs.echo.get_health_status", return_value=expected_status),
        patch("builtins.print") as print_mock,
    ):
        handler.handle(job)

    # Assert
    print_mock.assert_called_once_with(
        {
            "task": "echo_job",
            "payload": job,
            "core_status": expected_status,
        }
    )


# ---- JokeGenerationJob ----


def test_job_adapter_builds_joke_generation_job_from_payload() -> None:
    payload = {"type": "joke_generation", "job_id": 99}
    job = job_adapter(payload)
    assert isinstance(job, JokeGenerationJob)
    assert job.job_id == 99


def test_job_handler_map_points_joke_generation_to_handler() -> None:
    from learnwithai.tools.jokes.job import JokeGenerationJobHandler

    handler_class = get_job_handler_map()[JokeGenerationJob]
    handler = handler_class()
    assert isinstance(handler, JokeGenerationJobHandler)


# ---- RosterUploadJob ----


def test_job_adapter_builds_roster_upload_job_from_payload() -> None:
    # Arrange
    payload = {"type": "roster_upload", "job_id": 42}

    # Act
    job = job_adapter(payload)

    # Assert
    assert isinstance(job, RosterUploadJob)
    assert job.job_id == 42


def test_job_handler_map_points_roster_upload_to_handler() -> None:
    # Arrange
    handler_class = get_job_handler_map()[RosterUploadJob]

    # Act
    handler = handler_class()

    # Assert
    assert isinstance(handler, RosterUploadJobHandler)


def test_forbidden_job_queue_enqueue_raises() -> None:
    # Arrange
    queue = ForbiddenJobQueue()
    job = RosterUploadJob(job_id=1)

    # Act / Assert — enqueue must always raise
    with pytest.raises(RuntimeError, match="ForbiddenJobQueue.enqueue"):
        queue.enqueue(job)


def test_forbidden_job_queue_satisfies_job_queue_protocol() -> None:
    from learnwithai.interfaces import JobQueue

    assert isinstance(ForbiddenJobQueue(), JobQueue)


def test_roster_upload_job_handler_commits_on_success() -> None:
    # Arrange
    job_payload = RosterUploadJob(job_id=42)
    handler = RosterUploadJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_svc = MagicMock()
    mock_notifier = MagicMock()
    mock_async_job = MagicMock()
    mock_async_job.course_id = 1
    mock_async_job.created_by_pid = 111
    mock_async_job.kind = "roster_upload"
    mock_async_job.status = MagicMock(value="completed")
    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.services.roster_upload_service.RosterUploadService",
            return_value=mock_svc,
        ),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.jobs.roster_upload.UserRepository",
            return_value=MagicMock(),
        ),
        patch(
            "learnwithai.jobs.roster_upload.MembershipRepository",
            return_value=MagicMock(),
        ),
        patch(
            "learnwithai.jobs.roster_upload.AsyncJobRepository",
            return_value=MagicMock(),
        ),
        patch(
            "learnwithai.jobs.roster_upload.ForbiddenJobQueue",
            return_value=MagicMock(),
        ),
        patch("learnwithai.config.get_settings"),
    ):
        handler.handle(job_payload)

    # Assert
    mock_svc.process_upload.assert_called_once_with(42)
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


def test_roster_upload_job_handler_rolls_back_and_marks_failed_on_error() -> None:
    # Arrange
    job_payload = RosterUploadJob(job_id=42)
    handler = RosterUploadJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_svc = MagicMock()
    mock_svc.process_upload.side_effect = RuntimeError("boom")
    mock_notifier = MagicMock()
    mock_async_job = MagicMock()
    mock_async_job.course_id = 1
    mock_async_job.created_by_pid = 111
    mock_async_job.kind = "roster_upload"
    mock_async_job.status = MagicMock(value="failed")
    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.services.roster_upload_service.RosterUploadService",
            return_value=mock_svc,
        ),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.jobs.roster_upload.UserRepository",
            return_value=MagicMock(),
        ),
        patch(
            "learnwithai.jobs.roster_upload.MembershipRepository",
            return_value=MagicMock(),
        ),
        patch(
            "learnwithai.jobs.roster_upload.AsyncJobRepository",
            return_value=MagicMock(),
        ),
        patch(
            "learnwithai.jobs.roster_upload.ForbiddenJobQueue",
            return_value=MagicMock(),
        ),
        patch("learnwithai.config.get_settings"),
        pytest.raises(RuntimeError, match="boom"),
    ):
        handler.handle(job_payload)

    # Assert
    mock_session.rollback.assert_called_once()
    # Base handler marks failed via AsyncJobRepository, not via the service
    assert mock_async_job_repo_instance.update.call_count >= 1


# ---- NoOpJobNotifier ----


def test_noop_job_notifier_satisfies_job_notifier_protocol() -> None:
    from learnwithai.interfaces import JobNotifier
    from learnwithai.jobs import NoOpJobNotifier

    assert isinstance(NoOpJobNotifier(), JobNotifier)


def test_noop_job_notifier_discards_update_silently() -> None:
    from learnwithai.interfaces import JobUpdate
    from learnwithai.jobs import NoOpJobNotifier

    # Arrange
    notifier = NoOpJobNotifier()
    update = JobUpdate(
        job_id=1, course_id=1, user_id=111, kind="roster_upload", status="completed"
    )

    # Act — should not raise
    notifier.notify(update)


def test_roster_upload_handler_notify_skips_when_job_not_found() -> None:
    """Covers the branch where _notify's get_by_id returns None (87->exit)."""
    handler = RosterUploadJobHandler()
    mock_notifier = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = None

    # Act — should not raise, should not call notify
    handler._notify(mock_notifier, 999, mock_repo)

    mock_notifier.notify.assert_not_called()


def test_base_handler_notify_swallows_exceptions() -> None:
    """Covers the except branch in _notify."""
    handler = RosterUploadJobHandler()
    mock_notifier = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_by_id.side_effect = RuntimeError("db down")

    # Act — should not raise
    handler._notify(mock_notifier, 999, mock_repo)

    mock_notifier.notify.assert_not_called()


def test_base_handler_mark_failed_swallows_exceptions() -> None:
    """Covers the except branch in _mark_failed."""
    handler = RosterUploadJobHandler()
    mock_repo = MagicMock()
    mock_repo.get_by_id.side_effect = RuntimeError("db down")

    # Act — should not raise
    handler._mark_failed(999, mock_repo)


def test_base_handler_mark_failed_skips_when_job_not_found() -> None:
    """Covers the branch where _mark_failed's get_by_id returns None."""
    handler = RosterUploadJobHandler()
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = None

    # Act — should not raise
    handler._mark_failed(999, mock_repo)

    mock_repo.update.assert_not_called()


def test_base_handler_set_processing_skips_when_job_not_found() -> None:
    """Covers the branch where _set_processing's get_by_id returns None."""
    handler = RosterUploadJobHandler()
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = None
    mock_session = MagicMock()
    mock_notifier = MagicMock()

    # Act — should not raise
    handler._set_processing(999, mock_repo, mock_session, mock_notifier)

    mock_repo.update.assert_not_called()
    mock_session.flush.assert_not_called()


def test_base_handler_build_notifier_creates_rabbitmq_notifier() -> None:
    """Covers the default _build_notifier implementation."""
    handler = RosterUploadJobHandler()
    mock_settings = MagicMock()
    mock_settings.effective_rabbitmq_url = "amqp://test"

    with patch(
        "learnwithai_jobqueue.rabbitmq_job_notifier.RabbitMQJobNotifier",
    ) as mock_cls:
        notifier = handler._build_notifier(mock_settings)

    mock_cls.assert_called_once_with("amqp://test")
    assert notifier is mock_cls.return_value


def test_notify_includes_user_id_from_created_by_pid() -> None:
    """Verifies _notify populates user_id from the AsyncJob's created_by_pid."""
    from learnwithai.interfaces import JobUpdate

    handler = RosterUploadJobHandler()
    mock_notifier = MagicMock()
    mock_async_job = MagicMock()
    mock_async_job.course_id = 5
    mock_async_job.created_by_pid = 999
    mock_async_job.kind = "roster_upload"
    mock_async_job.status = MagicMock(value="completed")
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = mock_async_job

    handler._notify(mock_notifier, 42, mock_repo)

    mock_notifier.notify.assert_called_once()
    update: JobUpdate = mock_notifier.notify.call_args[0][0]
    assert update.job_id == 42
    assert update.course_id == 5
    assert update.user_id == 999
    assert update.kind == "roster_upload"
    assert update.status == "completed"
