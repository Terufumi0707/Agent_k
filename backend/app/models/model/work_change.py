from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class WorkChange(BaseModel):
    work_type: Optional[str] = None
    desired_date: Optional[str] = None
