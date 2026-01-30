from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel

from app.models.model.order_info import OrderInfo


class IntakeResponse(BaseModel):
    session_id: str
    status: Literal["need_more_info", "completed", "invalid_request"]
    message: str
    missing_fields: List[str]
    questions: List[str]
    order_info: Optional[OrderInfo] = None
    assistant_message: Optional[str] = None
