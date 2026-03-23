"""Pydantic models for course-related API requests and responses."""

from pydantic import BaseModel, ConfigDict

from learnwithai.tables.membership import MembershipState, MembershipType


class CourseMembership(BaseModel):
    """Represents the caller's membership for a returned course."""

    model_config = ConfigDict(from_attributes=True)

    type: MembershipType
    state: MembershipState


class CourseResponse(BaseModel):
    """Represents a course returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    term: str
    section: str
    membership: CourseMembership


class CreateCourseRequest(BaseModel):
    """Payload for creating a new course."""

    name: str
    term: str
    section: str


class AddMemberRequest(BaseModel):
    """Payload for adding a member to a course."""

    pid: int
    type: MembershipType


class MembershipResponse(BaseModel):
    """Represents a membership returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    user_pid: int
    course_id: int
    type: MembershipType
    state: MembershipState
