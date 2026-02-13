from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OrderStatus(str, Enum):
    DELIVERY = "DELIVERY"
    COORDINATE = "COORDINATE"
    BACKYARD = "BACKYARD"


@dataclass
class Order:
    id: str
    current_status: OrderStatus

