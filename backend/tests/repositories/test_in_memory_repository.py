from __future__ import annotations

from datetime import datetime

from src.domain.models import InputType, Job, JobStatus, MinuteCandidate
from src.repositories.in_memory_store import InMemoryStore


def _job(job_id: str, transcript: str = "t") -> Job:
    now = datetime.utcnow()
    return Job(
        id=job_id,
        input_type=InputType.TRANSCRIPT,
        status=JobStatus.WAITING_FOR_REVIEW,
        created_at=now,
        updated_at=now,
        transcript=transcript,
        candidates=[MinuteCandidate.from_dict({"会議概要": "案"})],
    )


def test_save_job():
    repo = InMemoryStore()
    job = _job("job-1")

    saved = repo.save(job)

    assert saved.id == "job-1"
    assert "job-1" in repo.jobs


def test_get_job():
    repo = InMemoryStore()
    repo.save(_job("job-2"))

    found = repo.get("job-2")

    assert found is not None
    assert found.id == "job-2"


def test_get_updated_job_after_resave():
    repo = InMemoryStore()
    job = _job("job-3", transcript="before")
    repo.save(job)
    job.transcript = "after"
    repo.save(job)

    found = repo.get("job-3")

    assert found is not None
    assert found.transcript == "after"


def test_get_missing_job_returns_none():
    repo = InMemoryStore()

    assert repo.get("missing") is None
