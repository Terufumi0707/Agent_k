from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.enums.input_type import InputType
from src.domain.enums.job_status import JobStatus


class Job(BaseModel):
    id: str
    status: JobStatus
    input_type: InputType
    workflow_name: str
    created_at: datetime
    updated_at: datetime


class JobStep(BaseModel):
    job_id: str
    step_name: str
    status: JobStatus
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)


class DraftVersion(BaseModel):
    job_id: str
    version_no: int
    content: dict[str, Any]
    created_at: datetime


class Feedback(BaseModel):
    job_id: str
    target_version_no: int
    feedback_type: str
    feedback_text: str
    created_at: datetime


class Artifact(BaseModel):
    job_id: str
    artifact_type: str
    file_path: str
    mime_type: str
