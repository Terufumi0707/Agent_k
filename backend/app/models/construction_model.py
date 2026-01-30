from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class ConstructionModel:
    id: int
    entry_id: str
    work_type: str
    work_date: date
