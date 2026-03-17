"""Public API models for authenticated user profile responses."""

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    """Represents the authenticated user profile returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    given_name: str
    family_name: str
    email: str
