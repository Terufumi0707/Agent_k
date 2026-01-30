from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.models.model.work_change import WorkChange


class IntakeNextRequest(BaseModel):
    session_id: str
    a_number: Optional[str] = None
    entry_id: Optional[str] = None
    work_changes: Optional[List[WorkChange]] = None
    fetch_current_order: Optional[bool] = None
    message: Optional[str] = None
