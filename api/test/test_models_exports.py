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
        "IyowActivityResponse",
        "IyowSubmissionResponse",
        "JokeResponse",
        "MembershipResponse",
        "PaginatedRosterResponse",
        "RosterMemberResponse",
        "RosterUploadResponse",
        "RosterUploadStatusResponse",
        "StudentSubmissionRow",
        "SubmitIyowRequest",
        "UpdateCourseRequest",
        "UpdateIyowActivityRequest",
        "UpdateProfileRequest",
        "UserProfile",
    }

    for export_name in models.__all__:
        assert getattr(models, export_name) is not None
