from ..db import Session
from ..models.user import User
from sqlmodel import select, col


class UserRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, user_id: str) -> User | None:
        query = select(User).where(col(User.id) == user_id)
        return self._session.exec(query).one_or_none()

    def get_by_pid(self, pid: str) -> User | None:
        query = select(User).where(col(User.pid) == pid)
        return self._session.exec(query).one_or_none()

    def register_user(self, new_user: User) -> User:
        self._session.add(new_user)
        self._session.flush()
        self._session.refresh(new_user)
        return new_user
