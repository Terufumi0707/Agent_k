from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class InputType(str, Enum):
    AUDIO = "audio"
    TRANSCRIPT = "transcript"


class JobStatus(str, Enum):
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    COMPLETED = "COMPLETED"


@dataclass
class MinuteCandidate:
    content: dict[str, Any]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> MinuteCandidate:
        return cls(content=dict(value))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.content)


def to_minute_candidates(values: Iterable[dict[str, Any]]) -> list[MinuteCandidate]:
    return [MinuteCandidate.from_dict(value) for value in values]


def minute_candidates_to_dicts(candidates: Iterable[MinuteCandidate]) -> list[dict[str, Any]]:
    return [candidate.to_dict() for candidate in candidates]


@dataclass
class Job:
    id: str
    input_type: InputType
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    transcript: str
    candidates: list[MinuteCandidate]
    selected_candidate: MinuteCandidate | None = None
    artifact_path: str | None = None
    review_comments: list[str] = field(default_factory=list)
