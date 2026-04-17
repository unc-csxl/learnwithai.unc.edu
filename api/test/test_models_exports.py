# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for the API model barrel exports."""

from __future__ import annotations

import api.models as models


def test_api_models_exports_expected_symbols() -> None:
    assert set(models.__all__) == {
        "ActivityResponse",
        "AddMemberRequest",
        "AsyncJobInfo",
        "CourseMembership",
        "CourseResponse",
        "CreateCourseRequest",
        "CreateIyowActivityRequest",
        "CreateJokeRequest",
        "GrantOperatorRequest",
        "ImpersonationTokenResponse",
        "IyowActivityResponse",
        "IyowStudentSubmissionRow",
        "IyowSubmissionResponse",
        "JobControlOverviewResponse",
        "JobFailuresResponse",
        "JokeResponse",
        "MembershipResponse",
        "OperatorProfile",
        "OperatorResponse",
        "PaginatedRosterResponse",
        "QueueMessagePreviewResponse",
        "QueueInfoResponse",
        "RosterMemberResponse",
        "RosterUploadResponse",
        "RosterUploadStatusResponse",
        "StudentRosterIdentity",
        "SubmitIyowRequest",
        "UpdateCourseRequest",
        "UpdateIyowActivityRequest",
        "UpdateMemberRoleRequest",
        "UpdateOperatorRoleRequest",
        "UpdateProfileRequest",
        "UsageMetricsResponse",
        "UserProfile",
        "WorkerInfoResponse",
        "UserSearchResult",
    }

    for export_name in models.__all__:
        assert getattr(models, export_name) is not None
