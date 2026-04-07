# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Integration tests for the joke repository."""

from __future__ import annotations

import pytest
from learnwithai.repositories.async_job_repository import AsyncJobRepository
from learnwithai.tables.async_job import AsyncJob
from learnwithai.tables.course import Course, Term
from learnwithai.tables.user import User
from learnwithai.tools.jokes.repository import JokeRepository
from learnwithai.tools.jokes.tables import Joke
from sqlmodel import Session

TEST_PID = 123456789


def _seed_user(session: Session) -> User:
    user = User(pid=TEST_PID, name="Test User", onyen="testuser")
    session.add(user)
    session.flush()
    return user


def _seed_course(session: Session) -> Course:
    course = Course(course_number="COMP101", name="Intro to CS", term=Term.FALL, year=2026)
    session.add(course)
    session.flush()
    return course


def _seed_async_job(session: Session, course_id: int) -> AsyncJob:
    repo = AsyncJobRepository(session)
    return repo.create(
        AsyncJob(
            course_id=course_id,
            created_by_pid=TEST_PID,
            kind="joke_generation",
            input_data={},
        )
    )


# --- create ---


@pytest.mark.integration
def test_create_persists_and_returns_joke(session: Session) -> None:
    _seed_user(session)
    course = _seed_course(session)
    async_job = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    repo = JokeRepository(session)
    joke = Joke(
        course_id=course.id,  # type: ignore[arg-type]
        created_by_pid=TEST_PID,
        prompt="Jokes about recursion",
        async_job_id=async_job.id,
    )

    result = repo.create(joke)

    assert result.id is not None
    assert result.course_id == course.id
    assert result.created_by_pid == TEST_PID
    assert result.prompt == "Jokes about recursion"
    assert result.jokes == []
    assert result.async_job_id == async_job.id
    assert result.created_at is not None
    assert result.updated_at is not None


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_joke(session: Session) -> None:
    _seed_user(session)
    course = _seed_course(session)
    async_job = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    repo = JokeRepository(session)
    created = repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="topic",
            async_job_id=async_job.id,
        )
    )

    result = repo.get_by_id(created.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.id == created.id


@pytest.mark.integration
def test_get_by_id_returns_none_for_missing(session: Session) -> None:
    repo = JokeRepository(session)

    assert repo.get_by_id(9999) is None


# --- get_by_async_job_id ---


@pytest.mark.integration
def test_get_by_async_job_id_returns_joke(session: Session) -> None:
    _seed_user(session)
    course = _seed_course(session)
    async_job = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    repo = JokeRepository(session)
    created = repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="topic",
            async_job_id=async_job.id,
        )
    )

    result = repo.get_by_async_job_id(async_job.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.id == created.id


@pytest.mark.integration
def test_get_by_async_job_id_returns_none_for_missing(session: Session) -> None:
    repo = JokeRepository(session)

    assert repo.get_by_async_job_id(9999) is None


# --- list_by_course ---


@pytest.mark.integration
def test_list_by_course_returns_matching_jokes(session: Session) -> None:
    _seed_user(session)
    course = _seed_course(session)
    repo = JokeRepository(session)
    job1 = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    job2 = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="first",
            async_job_id=job1.id,
        )
    )
    repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="second",
            async_job_id=job2.id,
        )
    )

    results = repo.list_by_course(course.id)  # type: ignore[arg-type]

    assert len(results) == 2


@pytest.mark.integration
def test_list_by_course_returns_empty_when_none(session: Session) -> None:
    repo = JokeRepository(session)

    assert repo.list_by_course(9999) == []


# --- list_by_course_with_jobs ---


@pytest.mark.integration
def test_list_by_course_with_jobs_returns_jokes_with_preloaded_jobs(session: Session) -> None:
    _seed_user(session)
    course = _seed_course(session)
    repo = JokeRepository(session)
    job1 = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    job2 = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="first",
            async_job_id=job1.id,
        )
    )
    repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="second",
            async_job_id=job2.id,
        )
    )

    results = repo.list_by_course_with_jobs(course.id)  # type: ignore[arg-type]

    assert len(results) == 2
    for joke in results:
        assert isinstance(joke, Joke)
        assert isinstance(joke.async_job, AsyncJob)


@pytest.mark.integration
def test_list_by_course_with_jobs_returns_none_for_missing_job(session: Session) -> None:
    _seed_user(session)
    course = _seed_course(session)
    repo = JokeRepository(session)
    repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="no job",
            async_job_id=None,
        )
    )

    results = repo.list_by_course_with_jobs(course.id)  # type: ignore[arg-type]

    assert len(results) == 1
    joke = results[0]
    assert isinstance(joke, Joke)
    assert joke.async_job is None


@pytest.mark.integration
def test_list_by_course_with_jobs_returns_empty_when_none(session: Session) -> None:
    repo = JokeRepository(session)

    assert repo.list_by_course_with_jobs(9999) == []


# --- update ---


@pytest.mark.integration
def test_update_persists_changes(session: Session) -> None:
    _seed_user(session)
    course = _seed_course(session)
    async_job = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    repo = JokeRepository(session)
    created = repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="topic",
            async_job_id=async_job.id,
        )
    )

    created.jokes = ["Joke A", "Joke B"]
    result = repo.update(created)

    assert result.jokes == ["Joke A", "Joke B"]


# --- delete ---


@pytest.mark.integration
def test_delete_removes_joke(session: Session) -> None:
    _seed_user(session)
    course = _seed_course(session)
    async_job = _seed_async_job(session, course.id)  # type: ignore[arg-type]
    repo = JokeRepository(session)
    created = repo.create(
        Joke(
            course_id=course.id,  # type: ignore[arg-type]
            created_by_pid=TEST_PID,
            prompt="topic",
            async_job_id=async_job.id,
        )
    )

    repo.delete(created)

    assert repo.get_by_id(created.id) is None  # type: ignore[arg-type]
