"""Pydantic models for the IYOW feedback job payload."""

from typing import Literal

from ...interfaces import TrackedJob

IYOW_FEEDBACK_KIND = "iyow_feedback"


class IyowFeedbackJob(TrackedJob):
    """Dramatiq job payload for IYOW feedback generation."""

    type: Literal["iyow_feedback"] = "iyow_feedback"
