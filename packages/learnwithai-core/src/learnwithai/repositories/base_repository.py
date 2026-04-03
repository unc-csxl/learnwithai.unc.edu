"""Shared SQLModel repository primitives."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlmodel import SQLModel

from ..db import Session

ModelT = TypeVar("ModelT", bound=SQLModel)
IdentifierT = TypeVar("IdentifierT")


class BaseRepository(ABC, Generic[ModelT, IdentifierT]):
    """Abstract base repository for shared SQLModel CRUD operations."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write persisted models.
        """
        self._session = session

    @property
    @abstractmethod
    def model_type(self) -> type[ModelT]:
        """Returns the SQLModel class managed by this repository."""

    def create(self, model: ModelT) -> ModelT:
        """Persists a new model and reloads database defaults.

        Args:
            model: Model instance to insert.

        Returns:
            The persisted model with refreshed database state.
        """
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return model

    def get_by_id(self, model_id: IdentifierT) -> ModelT | None:
        """Looks up a model by primary key.

        Args:
            model_id: Primary key value for the target model.

        Returns:
            The matching model when found; otherwise, ``None``.
        """
        return self._session.get(self.model_type, model_id)

    def update(self, model: ModelT) -> ModelT:
        """Persists changes to an existing model and refreshes state.

        Args:
            model: Model instance with updated fields.

        Returns:
            The updated model with refreshed database state.
        """
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return model

    def delete(self, model: ModelT) -> None:
        """Deletes a persisted model.

        Args:
            model: Model instance to remove.
        """
        self._session.delete(model)
        self._session.flush()
