from __future__ import annotations

from pydantic import BaseModel


class AutonomousNextRequest(BaseModel):
    session_id: str
    message: str
