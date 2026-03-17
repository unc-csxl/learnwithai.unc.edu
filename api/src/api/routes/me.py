"""Authenticated user profile routes."""

from fastapi import APIRouter

from ..dependency_injection import CurrentUserDI
from ..models import UserProfile

router = APIRouter()


@router.get("/me")
def get_current_user_profile(user: CurrentUserDI) -> UserProfile:
    """Returns the authenticated user's profile payload.

    Args:
        user: Authenticated user resolved from the bearer token.

    Returns:
        A UserProfile model for the API.
    """
    return UserProfile.model_validate(user.model_dump(mode="json"))
