from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class OrderInfo(BaseModel):
    main_a_number: str
    backup_a_number: Optional[str] = None
    main_work_types: List[str]
    main_work_date: Optional[str] = None
    backup_work_types: List[str]
    backup_work_date: Optional[str] = None
