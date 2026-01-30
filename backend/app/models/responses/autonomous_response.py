from __future__ import annotations

from typing import Dict, Literal, Optional

from pydantic import BaseModel


class AutonomousResponse(BaseModel):
    session_id: str
    status: Literal["need_more_info", "completed", "invalid_request"]
    message: str
    question: Optional[str] = None
    result: Optional[Dict[str, object]] = None
