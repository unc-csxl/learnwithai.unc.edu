"""Authenticated user profile routes."""

from fastapi import APIRouter

from ..dependency_injection import CurrentUserDI
from ..models import UserProfile

router = APIRouter(prefix="", tags=["Authentication"])


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get the authenticated user profile",
    response_description="Profile details for the authenticated user.",
    responses={401: {"description": "Bearer token is missing, invalid, or expired."}},
)
def get_current_user_profile(user: CurrentUserDI) -> UserProfile:
    """Returns the authenticated user's profile payload.

    Args:
        user: Authenticated user resolved from the bearer token.

    Returns:
        A UserProfile model for the API.
    """
    return UserProfile.model_validate(user.model_dump(mode="json"))
