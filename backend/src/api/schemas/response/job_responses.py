from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.domain.enums.input_type import InputType
from src.domain.enums.job_status import JobStatus


class ErrorResponse(BaseModel):
    code: str
    message: str


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    input_type: InputType
    workflow_name: str
    created_at: datetime
    updated_at: datetime


class CandidateResponse(BaseModel):
    version_no: int
    content: dict[str, Any]


class ArtifactResponse(BaseModel):
    artifact_type: str
    file_path: str
    mime_type: str
