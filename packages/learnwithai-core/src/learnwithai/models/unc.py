from pydantic import BaseModel


class UNCDirectorySearch(BaseModel):
    pid: str = ""
    displayName: str = ""
    snIterator: list[str] = []
    givenNameIterator: list[str] = []
    mailIterator: list[str] = []
