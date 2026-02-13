from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class OrderStatus(str, Enum):
    DELIVERY = "DELIVERY"
    COORDINATE = "COORDINATE"
    BACKYARD = "BACKYARD"


@dataclass
class Order:
    id: str
    session_id: str
    current_status: OrderStatus
    created_at: datetime
    updated_at: datetime
    n_number: str | None = None
    web_entry_id: str | None = None

    @property
    def status(self) -> OrderStatus:
        return self.current_status

    @classmethod
    def create(cls, session_id: str, current_status: OrderStatus) -> "Order":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid4()),
            session_id=session_id,
            current_status=current_status,
            created_at=now,
            updated_at=now,
        )
