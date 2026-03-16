"""Pydantic models for UNC directory responses."""

from pydantic import BaseModel


class UNCDirectorySearch(BaseModel):
    """Represents a single UNC directory search result."""

    pid: str = ""
    displayName: str = ""
    snIterator: list[str] = []
    givenNameIterator: list[str] = []
    mailIterator: list[str] = []
