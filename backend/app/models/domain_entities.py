from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.models.domain_value_objects import WorkType


@dataclass(frozen=True)
class Construction:
    work_type: WorkType
    work_date: date


@dataclass(frozen=True)
class Entry:
    entry_id: str
    constructions: list[Construction] = field(default_factory=list)
