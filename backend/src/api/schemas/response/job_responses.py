from datetime import datetime
from typing import Any

from pydantic import BaseModel, RootModel

from src.domain.models import InputType, Job, JobStatus, MinuteCandidate


class MinuteCandidateResponse(RootModel[dict[str, Any]]):
    @classmethod
    def from_domain(cls, candidate: MinuteCandidate) -> MinuteCandidateResponse:
        return cls(candidate.to_dict())


class JobResponse(BaseModel):
    id: str
    input_type: InputType
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    transcript: str
    candidates: list[MinuteCandidateResponse]
    selected_candidate: MinuteCandidateResponse | None
    artifact_path: str | None

    @classmethod
    def from_domain(cls, job: Job) -> JobResponse:
        return cls(
            id=job.id,
            input_type=job.input_type,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
            transcript=job.transcript,
            candidates=[MinuteCandidateResponse.from_domain(c) for c in job.candidates],
            selected_candidate=(
                MinuteCandidateResponse.from_domain(job.selected_candidate)
                if job.selected_candidate
                else None
            ),
            artifact_path=job.artifact_path,
        )
