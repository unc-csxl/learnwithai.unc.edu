# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for the JobControlService."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from learnwithai.errors import AuthorizationError
from learnwithai.services.job_control_service import (
    JobControlOverview,
    JobControlService,
    JobFailures,
    QueueInfo,
    QueueMessagePreview,
    RecentFailedJob,
    WorkerInfo,
)


def _stub_user(pid: int = 111111111) -> MagicMock:
    mock = MagicMock()
    mock.pid = pid
    return mock


def _build_service(
    queues: list[dict] | None = None,
    consumers: list[dict] | None = None,
    overview: dict | None = None,
) -> tuple[JobControlService, MagicMock, MagicMock, MagicMock]:
    """Builds a JobControlService with mocked dependencies.

    Returns:
        Tuple of (service, session_mock, operator_svc_mock, rabbitmq_mock).
    """
    session = MagicMock()
    operator_svc = MagicMock()
    rabbitmq = MagicMock()
    rabbitmq.get_queues.return_value = queues or []
    rabbitmq.get_consumers.return_value = consumers or []
    rabbitmq.get_overview.return_value = overview or {}
    svc = JobControlService(session, operator_svc, rabbitmq)
    return svc, session, operator_svc, rabbitmq


class TestGetOverview:
    def test_returns_overview_with_queue_stats(self) -> None:
        svc, _, _, _ = _build_service(
            queues=[
                {"name": "default", "messages_ready": 5, "messages_unacknowledged": 2, "consumers": 3},
                {"name": "default.DQ", "messages_ready": 1, "messages_unacknowledged": 0, "consumers": 0},
                {"name": "default.XQ", "messages_ready": 2, "messages_unacknowledged": 0, "consumers": 0},
            ],
            overview={"alarms": [{"resource": "disk"}]},
        )

        result = svc.get_overview(_stub_user())

        assert isinstance(result, JobControlOverview)
        assert result.total_queued == 8
        assert result.total_unacked == 2
        assert result.dlq_depth == 2
        assert result.retry_depth == 1
        assert result.consumers_online == 3
        assert result.broker_alarms == ["disk"]

    def test_enforces_view_jobs_permission(self) -> None:
        svc, _, operator_svc, _ = _build_service()
        operator_svc.require_permission.side_effect = AuthorizationError("denied")

        with pytest.raises(AuthorizationError):
            svc.get_overview(_stub_user())

    def test_empty_queues_returns_zeros(self) -> None:
        svc, _, _, _ = _build_service(queues=[], overview={})

        result = svc.get_overview(_stub_user())

        assert result.total_queued == 0
        assert result.consumers_online == 0
        assert result.broker_alarms == []


class TestGetQueues:
    def test_returns_queue_list(self) -> None:
        svc, _, _, _ = _build_service(
            queues=[
                {
                    "name": "default",
                    "messages_ready": 3,
                    "messages_unacknowledged": 1,
                    "consumers": 2,
                    "message_stats": {"ack_details": {"rate": 1.5}},
                },
                {
                    "name": "default.DQ",
                    "messages_ready": 0,
                    "messages_unacknowledged": 0,
                    "consumers": 0,
                },
            ],
        )

        result = svc.get_queues(_stub_user())

        assert len(result) == 2
        assert isinstance(result[0], QueueInfo)
        assert result[0].name == "default"
        assert result[0].ack_rate == 1.5
        assert result[0].is_dlq is False
        assert result[1].is_retry is True

    def test_parses_retry_queue_arguments(self) -> None:
        svc, _, _, _ = _build_service(
            queues=[
                {
                    "name": "default.DQ",
                    "messages_ready": 2,
                    "messages_unacknowledged": 0,
                    "consumers": 0,
                    "arguments": {
                        "x-message-ttl": "30000",
                        "x-dead-letter-exchange": "",
                        "x-dead-letter-routing-key": "default",
                    },
                },
            ],
        )

        result = svc.get_queues(_stub_user())

        assert result[0].is_retry is True
        assert result[0].message_ttl_ms == 30000
        assert result[0].dead_letter_exchange == ""
        assert result[0].dead_letter_routing_key == "default"

    def test_ignores_non_numeric_or_non_text_arguments(self) -> None:
        svc, _, _, _ = _build_service(
            queues=[
                {
                    "name": "default.DQ",
                    "messages_ready": 1,
                    "messages_unacknowledged": 0,
                    "consumers": 0,
                    "arguments": {
                        "x-message-ttl": "soon",
                        "x-dead-letter-exchange": {"name": "default"},
                        "x-dead-letter-routing-key": False,
                    },
                },
            ],
        )

        result = svc.get_queues(_stub_user())

        assert result[0].message_ttl_ms is None
        assert result[0].dead_letter_exchange is None
        assert result[0].dead_letter_routing_key is None

    def test_handles_non_dict_arguments_payload(self) -> None:
        svc, _, _, _ = _build_service(
            queues=[
                {
                    "name": "default.DQ",
                    "messages_ready": 1,
                    "messages_unacknowledged": 0,
                    "consumers": 0,
                    "arguments": ["not", "a", "dict"],
                },
            ],
        )

        result = svc.get_queues(_stub_user())

        assert result[0].message_ttl_ms is None
        assert result[0].dead_letter_exchange is None
        assert result[0].dead_letter_routing_key is None

    def test_coerces_bool_and_float_retry_arguments(self) -> None:
        svc, _, _, _ = _build_service(
            queues=[
                {
                    "name": "default.DQ",
                    "messages_ready": 1,
                    "messages_unacknowledged": 0,
                    "consumers": 0,
                    "arguments": {
                        "x-message-ttl": 30_000.9,
                        "x-dead-letter-exchange": "",
                        "x-dead-letter-routing-key": True,
                    },
                },
                {
                    "name": "fallback.DQ",
                    "messages_ready": 1,
                    "messages_unacknowledged": 0,
                    "consumers": 0,
                    "arguments": {
                        "x-message-ttl": False,
                        "x-dead-letter-exchange": "retry-exchange",
                        "x-dead-letter-routing-key": "retry-key",
                    },
                },
            ],
        )

        result = svc.get_queues(_stub_user())

        assert result[0].message_ttl_ms == 30000
        assert result[0].dead_letter_exchange == ""
        assert result[0].dead_letter_routing_key is None
        assert result[0].is_retry is True
        assert result[1].message_ttl_ms is None
        assert result[1].dead_letter_exchange == "retry-exchange"
        assert result[1].dead_letter_routing_key == "retry-key"
        assert result[1].is_retry is True

    def test_enforces_view_jobs_permission(self) -> None:
        svc, _, operator_svc, _ = _build_service()
        operator_svc.require_permission.side_effect = AuthorizationError("denied")

        with pytest.raises(AuthorizationError):
            svc.get_queues(_stub_user())


class TestGetWorkers:
    def test_returns_worker_list(self) -> None:
        svc, _, _, _ = _build_service(
            consumers=[
                {
                    "consumer_tag": "worker.1",
                    "queue": {"name": "default"},
                    "channel_details": {"name": "ch-1"},
                    "prefetch_count": 1,
                },
            ],
        )

        result = svc.get_workers(_stub_user())

        assert len(result) == 1
        assert isinstance(result[0], WorkerInfo)
        assert result[0].consumer_tag == "worker.1"
        assert result[0].queue == "default"
        assert result[0].channel_details == "ch-1"

    def test_handles_non_dict_queue_field(self) -> None:
        svc, _, _, _ = _build_service(
            consumers=[
                {
                    "consumer_tag": "w.1",
                    "queue": "plain-string",
                    "channel_details": "ch",
                    "prefetch_count": 0,
                },
            ],
        )

        result = svc.get_workers(_stub_user())

        assert result[0].queue == ""
        assert result[0].channel_details == "ch"


class TestGetFailures:
    def test_returns_failure_summary(self) -> None:
        svc, session, _, _ = _build_service(
            queues=[{"name": "default.XQ", "messages_ready": 3}],
        )

        # Mock DB queries for failed jobs and error buckets
        failed_job = MagicMock()
        failed_job.id = 1
        failed_job.kind = "roster_upload"
        failed_job.course_id = 100
        failed_job.error_message = "Parse error"
        failed_job.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        failed_job.completed_at = datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc)

        exec_mock = MagicMock()
        # First call: failed jobs query
        first_result = MagicMock()
        first_result.all.return_value = [failed_job]
        # Second call: error buckets query
        second_result = MagicMock()
        second_result.all.return_value = [("roster_upload", 1)]
        exec_mock.side_effect = [first_result, second_result]
        session.exec = exec_mock

        result = svc.get_failures(_stub_user())

        assert isinstance(result, JobFailures)
        assert result.dlq_messages == 3
        assert len(result.recent_failed_jobs) == 1
        assert isinstance(result.recent_failed_jobs[0], RecentFailedJob)
        assert result.recent_failed_jobs[0].kind == "roster_upload"
        assert result.error_buckets == {"roster_upload": 1}


class TestPurgeQueue:
    def test_calls_rabbitmq_purge(self) -> None:
        svc, _, _, rabbitmq = _build_service()

        svc.purge_queue(_stub_user(), "default")

        rabbitmq.purge_queue.assert_called_once_with("default")

    def test_enforces_manage_operators_permission(self) -> None:
        svc, _, operator_svc, _ = _build_service()
        operator_svc.require_permission.side_effect = AuthorizationError("denied")

        with pytest.raises(AuthorizationError):
            svc.purge_queue(_stub_user(), "default")


class TestPeekQueueMessages:
    def test_returns_parsed_queue_preview(self) -> None:
        svc, _, _, rabbitmq = _build_service()
        rabbitmq.peek_queue_messages.return_value = [
            {
                "routing_key": "default.XQ",
                "payload": (
                    '{"queue_name":"default","actor_name":"job_queue","args":[{"job_id":3,'
                    '"type":"iyow_feedback"}],"kwargs":{},"options":{"retries":3,'
                    '"traceback":"Traceback\\nValueError: AsyncJob 3 not found"},'
                    '"message_id":"abc","message_timestamp":1775943548943}'
                ),
                "properties": {
                    "headers": {
                        "x-first-death-queue": "default",
                        "x-first-death-reason": "rejected",
                    }
                },
            }
        ]

        result = svc.peek_queue_messages(_stub_user(), "default.XQ", limit=1)

        rabbitmq.peek_queue_messages.assert_called_once_with("default.XQ", count=1)
        assert len(result) == 1
        assert isinstance(result[0], QueueMessagePreview)
        assert result[0].queue_name == "default"
        assert result[0].routing_key == "default.XQ"
        assert result[0].actor_name == "job_queue"
        assert result[0].job_id == 3
        assert result[0].job_type == "iyow_feedback"
        assert result[0].retries == 3
        assert result[0].source_queue == "default"
        assert result[0].death_reason == "rejected"
        assert result[0].error_summary == "ValueError: AsyncJob 3 not found"
        assert result[0].payload_preview == '{"args": [{"job_id": 3, "type": "iyow_feedback"}], "kwargs": {}}'
        assert result[0].enqueued_at == datetime.fromtimestamp(1775943548943 / 1000, tz=timezone.utc)

    def test_returns_requested_preview_page(self) -> None:
        svc, _, _, rabbitmq = _build_service()
        rabbitmq.peek_queue_messages.return_value = [
            {
                "routing_key": "default.XQ",
                "payload": '{"message_id":"one"}',
                "properties": {},
            },
            {
                "routing_key": "default.XQ",
                "payload": '{"message_id":"two"}',
                "properties": {},
            },
            {
                "routing_key": "default.XQ",
                "payload": '{"message_id":"three"}',
                "properties": {},
            },
            {
                "routing_key": "default.XQ",
                "payload": '{"message_id":"four"}',
                "properties": {},
            },
        ]

        result = svc.peek_queue_messages(_stub_user(), "default.XQ", limit=2, page=2)

        rabbitmq.peek_queue_messages.assert_called_once_with("default.XQ", count=4)
        assert [preview.message_id for preview in result] == ["three", "four"]

    def test_enforces_view_jobs_permission(self) -> None:
        svc, _, operator_svc, _ = _build_service()
        operator_svc.require_permission.side_effect = AuthorizationError("denied")

        with pytest.raises(AuthorizationError):
            svc.peek_queue_messages(_stub_user(), "default.XQ")

    def test_handles_unstructured_preview_payloads(self) -> None:
        svc, _, _, rabbitmq = _build_service()
        rabbitmq.peek_queue_messages.return_value = [
            {
                "routing_key": "default.XQ",
                "payload": {"unexpected": "object"},
                "properties": {"headers": []},
            },
            {
                "routing_key": "default.XQ",
                "payload": "not-json",
                "properties": {"headers": {"x-first-death-reason": 9}},
            },
            {
                "routing_key": "default.XQ",
                "payload": '["not", "a", "dict"]',
                "properties": {"headers": {"x-first-death-reason": 9}},
            },
            {
                "routing_key": "default.XQ",
                "payload": ('{"queue_name":"default","args":["plain"],"kwargs":[],"options":{"traceback":"  \\n"}}'),
                "properties": "not-a-dict",
            },
        ]

        result = svc.peek_queue_messages(_stub_user(), "default.XQ", limit=4)

        assert [preview.queue_name for preview in result[:3]] == ["default.XQ", "default.XQ", "default.XQ"]
        assert result[0].payload_preview == '{"args": [], "kwargs": {}}'
        assert result[0].actor_name is None
        assert result[0].enqueued_at is None
        assert result[1].death_reason is None
        assert result[1].job_id is None
        assert result[2].payload_preview == '{"args": [], "kwargs": {}}'
        assert result[3].queue_name == "default"
        assert result[3].job_type is None
        assert result[3].payload_preview == '{"args": ["plain"], "kwargs": {}}'
        assert result[3].error_summary is None
