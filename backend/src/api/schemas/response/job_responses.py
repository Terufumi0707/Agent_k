from datetime import datetime

from pydantic import BaseModel

from src.domain.models import InputType, JobStatus


class JobResponse(BaseModel):
    id: str
    input_type: InputType
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    transcript: str
    candidates: list[dict]
    selected_candidate: dict | None
    artifact_path: str | None
