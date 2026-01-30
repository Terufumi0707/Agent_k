from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class WorkTypeConfidence(BaseModel):
    name: str
    confidence: Literal["high", "medium", "low"]
