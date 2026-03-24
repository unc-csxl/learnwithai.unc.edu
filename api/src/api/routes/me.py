"""Authenticated user profile routes."""

from typing import Annotated

from fastapi import APIRouter, Body

from ..dependency_injection import AuthenticatedUserDI, UserRepositoryDI
from ..models import UpdateProfileRequest, UserProfile

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


@router.put(
    "/me",
    response_model=UserProfile,
    summary="Update the authenticated user profile",
    response_description="The updated profile.",
    responses={401: {"description": "Bearer token is missing, invalid, or expired."}},
)
def update_current_subject_profile(
    subject: AuthenticatedUserDI,
    body: Annotated[UpdateProfileRequest, Body()],
    user_repo: UserRepositoryDI,
) -> UserProfile:
    """Updates the authenticated subject's given and family name.

    The full display name is recomputed as ``given_name + " " + family_name``.

    Args:
        subject: Authenticated subject resolved from the bearer token.
        body: Profile update payload.
        user_repo: Repository used to persist the change.

    Returns:
        The updated user profile.
    """
    subject.given_name = body.given_name
    subject.family_name = body.family_name
    subject.name = f"{body.given_name} {body.family_name}"
    updated = user_repo.update_user(subject)
    return UserProfile.model_validate(updated.model_dump(mode="json"))
