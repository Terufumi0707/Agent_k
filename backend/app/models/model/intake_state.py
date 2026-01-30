from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.model.order_info import OrderInfo
from app.models.model.work_change import WorkChange


class IntakeState(BaseModel):
    session_id: str
    a_number: Optional[str] = None
    entry_id: Optional[str] = None
    work_changes: List[WorkChange] = Field(default_factory=list)
    fetch_current_order: bool = False
    order_info: Optional[OrderInfo] = None
    missing_fields: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    status: Literal["need_more_info", "completed", "invalid_request"] = "need_more_info"
    logs: List[str] = Field(default_factory=list)
    last_user_message: Optional[str] = None
    assistant_message: Optional[str] = None
