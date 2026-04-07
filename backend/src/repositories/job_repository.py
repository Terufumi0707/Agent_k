from __future__ import annotations

from typing import Protocol

from src.domain.models import Job


class JobRepository(Protocol):
    def save(self, job: Job) -> Job:
        ...

    def get(self, job_id: str) -> Job | None:
        ...
