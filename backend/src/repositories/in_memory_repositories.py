from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from src.domain.entities.models import Artifact, DraftVersion, Feedback, Job, JobStep


class InMemoryJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.steps: dict[str, list[JobStep]] = defaultdict(list)
        self.contexts: dict[str, dict] = defaultdict(dict)

    def save_job(self, job: Job) -> Job:
        self.jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def update_status(self, job_id: str, status) -> Job:
        job = self.jobs[job_id]
        job.status = status
        job.updated_at = datetime.utcnow()
        self.jobs[job_id] = job
        return job

    def add_step(self, step: JobStep) -> None:
        self.steps[step.job_id].append(step)

    def list_steps(self, job_id: str) -> list[JobStep]:
        return self.steps[job_id]

    def upsert_context(self, job_id: str, payload: dict) -> None:
        self.contexts[job_id].update(payload)

    def get_context(self, job_id: str) -> dict:
        return self.contexts[job_id]


class InMemoryDraftRepository:
    def __init__(self) -> None:
        self.items: dict[str, list[DraftVersion]] = defaultdict(list)

    def add(self, draft: DraftVersion) -> None:
        self.items[draft.job_id].append(draft)

    def list_by_job(self, job_id: str) -> list[DraftVersion]:
        return self.items[job_id]

    def get_version(self, job_id: str, version_no: int) -> DraftVersion | None:
        for item in self.items[job_id]:
            if item.version_no == version_no:
                return item
        return None


class InMemoryFeedbackRepository:
    def __init__(self) -> None:
        self.items: dict[str, list[Feedback]] = defaultdict(list)

    def add(self, feedback: Feedback) -> None:
        self.items[feedback.job_id].append(feedback)

    def list_by_job(self, job_id: str) -> list[Feedback]:
        return self.items[job_id]


class InMemoryArtifactRepository:
    def __init__(self) -> None:
        self.items: dict[str, list[Artifact]] = defaultdict(list)

    def add(self, artifact: Artifact) -> None:
        self.items[artifact.job_id].append(artifact)

    def get_latest(self, job_id: str, artifact_type: str) -> Artifact | None:
        result = [i for i in self.items[job_id] if i.artifact_type == artifact_type]
        return result[-1] if result else None
