# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Pydantic models for course-related API requests and responses."""

from learnwithai.tables.course import Term
from learnwithai.tables.membership import MembershipState, MembershipType
from pydantic import BaseModel, ConfigDict


class CourseMembership(BaseModel):
    """Represents the caller's membership for a returned course."""

    model_config = ConfigDict(from_attributes=True)

    type: MembershipType
    state: MembershipState


class CourseResponse(BaseModel):
    """Represents a course returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    course_number: str
    name: str
    description: str
    term: Term
    year: int
    membership: CourseMembership


class CreateCourseRequest(BaseModel):
    """Payload for creating a new course."""

    course_number: str
    name: str
    description: str = ""
    term: Term
    year: int


class UpdateCourseRequest(BaseModel):
    """Payload for updating an existing course."""

    course_number: str
    name: str
    description: str = ""
    term: Term
    year: int


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


class RosterMemberResponse(BaseModel):
    """A roster entry combining membership and user details."""

    user_pid: int
    course_id: int
    type: MembershipType
    state: MembershipState
    given_name: str
    family_name: str
    email: str


class PaginatedRosterResponse(BaseModel):
    """Paginated wrapper around roster member entries."""

    items: list[RosterMemberResponse]
    total: int
    page: int
    page_size: int
