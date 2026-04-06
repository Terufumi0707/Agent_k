from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class InputType(str, Enum):
    AUDIO = "audio"
    TRANSCRIPT = "transcript"


class JobStatus(str, Enum):
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    COMPLETED = "COMPLETED"


@dataclass
class Job:
    id: str
    input_type: InputType
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    transcript: str
    candidates: list[dict]
    selected_candidate: dict | None = None
    artifact_path: str | None = None
    review_comments: list[str] = field(default_factory=list)
