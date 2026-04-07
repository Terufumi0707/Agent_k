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
    CREATED = "CREATED"
    DRAFTING = "DRAFTING"
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    COMPLETED = "COMPLETED"


@dataclass
class MinuteCandidate:
    sections: dict[str, Any] = field(default_factory=dict)
    raw_content: str | None = None
    _include_sections_field: bool = False
    _include_raw_content_field: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> MinuteCandidate:
        copied = dict(value)
        explicit_sections = copied.pop("sections", None)

        include_sections_field = isinstance(explicit_sections, dict)
        include_raw_content_field = "raw_content" in copied
        raw_content = copied.pop("raw_content", None)

        sections: dict[str, Any] = {}
        if isinstance(explicit_sections, dict):
            sections.update(explicit_sections)

        for key, item in copied.items():
            sections.setdefault(key, item)

        return cls(
            sections=sections,
            raw_content=(str(raw_content) if raw_content is not None else None),
            _include_sections_field=include_sections_field,
            _include_raw_content_field=include_raw_content_field,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.sections)
        if self._include_sections_field or self.raw_content is not None:
            payload["sections"] = dict(self.sections)
        if self._include_raw_content_field or self.raw_content is not None:
            payload["raw_content"] = self.raw_content
        return payload


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
