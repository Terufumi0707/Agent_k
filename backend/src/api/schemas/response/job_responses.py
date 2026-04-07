from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, RootModel, model_validator

from src.domain.models import InputType, Job, JobStatus, MinuteCandidate


class MinuteCandidatePayload(BaseModel):
    sections: dict[str, Any] | None = None
    raw_content: str | None = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def infer_sections_from_legacy_shape(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        if "sections" in value:
            return value

        legacy_sections = {k: v for k, v in value.items() if k != "raw_content"}
        return {**value, "sections": legacy_sections}


class MinuteCandidateResponse(RootModel[MinuteCandidatePayload]):
    @classmethod
    def from_domain(cls, candidate: MinuteCandidate) -> MinuteCandidateResponse:
        return cls(MinuteCandidatePayload.model_validate(candidate.to_dict()))


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
