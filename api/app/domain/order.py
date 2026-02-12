from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class RepositoryUnavailableError(Exception):
    pass


class NotFoundError(Exception):
    pass


class MultipleMatchesError(Exception):
    pass


@dataclass(frozen=True)
class ScheduledConstruction:
    construction_item_id: str
    normalized_type: str
    overview: str
    scheduled_date: str
    scheduled_time_slot: str


@dataclass(frozen=True)
class OrderRecord:
    n_number: str
    web_entry_id: str
    status: str
    last_updated: datetime
    construction: list[ScheduledConstruction]
