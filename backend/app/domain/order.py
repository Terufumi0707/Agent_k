from __future__ import annotations

from dataclasses import dataclass
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

    @classmethod
    def create(cls, session_id: str, current_status: OrderStatus) -> "Order":
        return cls(id=str(uuid4()), session_id=session_id, current_status=current_status)
