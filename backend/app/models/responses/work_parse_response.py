from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel

from app.models.model.work_type_confidence import WorkTypeConfidence


class WorkParseResponse(BaseModel):
    operation: Literal["change", "add", "delete", "confirm"]
    work_types: List[WorkTypeConfidence]
    date: str
    date_inferred: bool
    notes: str
