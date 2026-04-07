from __future__ import annotations

from src.domain.models import Job
from src.repositories.job_repository import JobRepository


class InMemoryStore(JobRepository):
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}

    def save(self, job: Job) -> Job:
        self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)
