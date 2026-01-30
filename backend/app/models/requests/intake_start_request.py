from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.models.model.work_change import WorkChange


class IntakeStartRequest(BaseModel):
    a_number: Optional[str] = None
    entry_id: Optional[str] = None
    work_changes: Optional[List[WorkChange]] = None
    fetch_current_order: bool = False
    message: Optional[str] = None
