from __future__ import annotations

from src.domain.models import Job


class InMemoryStore:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}

    def save(self, job: Job) -> Job:
        self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)
