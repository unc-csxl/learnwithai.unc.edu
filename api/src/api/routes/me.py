"""Authenticated user profile routes."""

from fastapi import APIRouter

from ..dependency_injection import AuthenticatedUserDI
from ..models import UserProfile

router = APIRouter(prefix="", tags=["Authentication"])


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get the authenticated user profile",
    response_description="Profile details for the authenticated user.",
    responses={401: {"description": "Bearer token is missing, invalid, or expired."}},
)
def get_current_subject_profile(subject: AuthenticatedUserDI) -> UserProfile:
    """Returns the authenticated subject's profile payload.

    Args:
        subject: Authenticated subject resolved from the bearer token.

    Returns:
        A UserProfile model for the API.
    """
    return UserProfile.model_validate(subject.model_dump(mode="json"))
