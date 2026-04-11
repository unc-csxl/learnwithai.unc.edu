# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Integration tests for OperatorRepository."""

from __future__ import annotations

import pytest
from learnwithai.repositories.operator_repository import OperatorRepository
from learnwithai.tables.operator import Operator, OperatorRole
from learnwithai.tables.user import User
from sqlmodel import Session


def _seed_user(session: Session, pid: int = 111111111, name: str = "Test User", onyen: str = "test") -> User:
    user = User(pid=pid, name=name, onyen=onyen)
    session.add(user)
    session.flush()
    return user


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_none_when_not_operator(session: Session) -> None:
    _seed_user(session)
    repo = OperatorRepository(session)

    result = repo.get_by_id(111111111)

    assert result is None


@pytest.mark.integration
def test_get_by_id_returns_operator_when_exists(session: Session) -> None:
    user = _seed_user(session)
    session.add(Operator(user_pid=user.pid, role=OperatorRole.ADMIN))
    session.flush()
    repo = OperatorRepository(session)

    result = repo.get_by_id(user.pid)

    assert result is not None
    assert result.user_pid == user.pid
    assert result.role == OperatorRole.ADMIN


# --- list_all ---


@pytest.mark.integration
def test_list_all_returns_empty_when_no_operators(session: Session) -> None:
    repo = OperatorRepository(session)

    result = repo.list_all()

    assert result == []


@pytest.mark.integration
def test_list_all_returns_all_operators(session: Session) -> None:
    user_a = _seed_user(session, pid=100000001, name="User A", onyen="usera")
    user_b = _seed_user(session, pid=100000002, name="User B", onyen="userb")
    session.add(Operator(user_pid=user_a.pid, role=OperatorRole.SUPERADMIN))
    session.add(Operator(user_pid=user_b.pid, role=OperatorRole.HELPDESK))
    session.flush()
    repo = OperatorRepository(session)

    result = repo.list_all()

    assert len(result) == 2
    pids = {op.user_pid for op in result}
    assert pids == {100000001, 100000002}


@pytest.mark.integration
def test_list_all_eagerly_loads_user(session: Session) -> None:
    user = _seed_user(session, pid=100000003, name="Eager User", onyen="eager")
    session.add(Operator(user_pid=user.pid, role=OperatorRole.ADMIN))
    session.flush()
    repo = OperatorRepository(session)

    result = repo.list_all()

    assert len(result) == 1
    assert result[0].user is not None
    assert result[0].user.name == "Eager User"


# --- create (inherited from BaseRepository) ---


@pytest.mark.integration
def test_create_persists_operator(session: Session) -> None:
    creator = _seed_user(session, pid=100000010, name="Creator", onyen="creator")
    target = _seed_user(session, pid=100000011, name="Target", onyen="target")
    repo = OperatorRepository(session)

    op = repo.create(
        Operator(
            user_pid=target.pid,
            role=OperatorRole.HELPDESK,
            created_by_pid=creator.pid,
        )
    )

    assert op.user_pid == target.pid
    assert op.role == OperatorRole.HELPDESK
    assert op.created_by_pid == creator.pid
    assert op.created_at is not None

    fetched = repo.get_by_id(target.pid)
    assert fetched is not None
    assert fetched.user_pid == op.user_pid


# --- update (inherited from BaseRepository) ---


@pytest.mark.integration
def test_update_changes_role(session: Session) -> None:
    user = _seed_user(session, pid=100000020, name="Updatable", onyen="updatable")
    session.add(Operator(user_pid=user.pid, role=OperatorRole.HELPDESK))
    session.flush()
    repo = OperatorRepository(session)

    op = repo.get_by_id(user.pid)
    assert op is not None
    op.role = OperatorRole.ADMIN
    updated = repo.update(op)

    assert updated.role == OperatorRole.ADMIN

    fetched = repo.get_by_id(user.pid)
    assert fetched is not None
    assert fetched.role == OperatorRole.ADMIN


# --- delete (inherited from BaseRepository) ---


@pytest.mark.integration
def test_delete_removes_operator(session: Session) -> None:
    user = _seed_user(session, pid=100000030, name="Deletable", onyen="deletable")
    session.add(Operator(user_pid=user.pid, role=OperatorRole.HELPDESK))
    session.flush()
    repo = OperatorRepository(session)

    op = repo.get_by_id(user.pid)
    assert op is not None
    repo.delete(op)

    assert repo.get_by_id(user.pid) is None
