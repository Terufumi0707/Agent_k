from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EntryModel:
    id: int
    entry_id: str
    created_at: datetime
    updated_at: datetime
