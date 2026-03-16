from typing import Annotated, TypeAlias
from fastapi import Depends
from .dependency_injection import SessionDI, JobQueueDI


class PublicContext:
    def __init__(self, session: SessionDI, job_queue: JobQueueDI):
        self.session = session
        self.job_queue = job_queue


class UserContext:
    def __init__(self, session: SessionDI, job_queue: JobQueueDI):
        self.session = session
        self.job_queue = job_queue


PublicContextDI: TypeAlias = Annotated[PublicContext, Depends()]
UserContextDI: TypeAlias = Annotated[UserContext, Depends()]
