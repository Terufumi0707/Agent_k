from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, Protocol

from app.domain.order import Order, OrderStatus


class OrderRepository(Protocol):
    def find_by_id(self, order_id: str) -> Optional[Order]:
        ...

    def find_by_session_id(self, session_id: str) -> Optional[Order]:
        ...

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        ...

    def list_all(self) -> list[Order]:
        ...

    def list_orders(self, sort: str = "updated_at_desc", limit: int = 100, offset: int = 0) -> list[Order]:
        ...

    def list_orders_by_status(
        self,
        status: OrderStatus,
        sort: str = "updated_at_desc",
        limit: int = 100,
        offset: int = 0,
    ) -> list[Order]:
        ...

    def save(self, order: Order) -> None:
        ...


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: list[Order] = []
        self.seed_defaults()

    def seed_defaults(self) -> None:
        base = datetime.now(timezone.utc)
        self._orders = [
            Order(
                id="order-delivery-001",
                session_id="session-delivery-001",
                current_status=OrderStatus.DELIVERY,
                created_at=base - timedelta(minutes=9),
                updated_at=base - timedelta(minutes=1),
            ),
            Order(
                id="order-delivery-002",
                session_id="session-delivery-002",
                current_status=OrderStatus.DELIVERY,
                created_at=base - timedelta(minutes=8),
                updated_at=base - timedelta(minutes=2),
            ),
            Order(
                id="order-delivery-003",
                session_id="session-delivery-003",
                current_status=OrderStatus.DELIVERY,
                created_at=base - timedelta(minutes=7),
                updated_at=base - timedelta(minutes=3),
            ),
            Order(
                id="order-coordinate-001",
                session_id="session-coordinate-001",
                current_status=OrderStatus.COORDINATE,
                created_at=base - timedelta(minutes=6),
                updated_at=base - timedelta(minutes=4),
            ),
            Order(
                id="order-coordinate-002",
                session_id="session-coordinate-002",
                current_status=OrderStatus.COORDINATE,
                created_at=base - timedelta(minutes=5),
                updated_at=base - timedelta(minutes=5),
            ),
            Order(
                id="order-coordinate-003",
                session_id="session-coordinate-003",
                current_status=OrderStatus.COORDINATE,
                created_at=base - timedelta(minutes=4),
                updated_at=base - timedelta(minutes=6),
            ),
            Order(
                id="order-backyard-001",
                session_id="session-backyard-001",
                current_status=OrderStatus.BACKYARD,
                created_at=base - timedelta(minutes=3),
                updated_at=base - timedelta(minutes=7),
            ),
            Order(
                id="order-backyard-002",
                session_id="session-backyard-002",
                current_status=OrderStatus.BACKYARD,
                created_at=base - timedelta(minutes=2),
                updated_at=base - timedelta(minutes=8),
            ),
            Order(
                id="order-backyard-003",
                session_id="session-backyard-003",
                current_status=OrderStatus.BACKYARD,
                created_at=base - timedelta(minutes=1),
                updated_at=base - timedelta(minutes=9),
            ),
        ]

    def find_by_id(self, order_id: str) -> Optional[Order]:
        for order in self._orders:
            if order.id == order_id:
                return order
        return None

    def find_by_session_id(self, session_id: str) -> Optional[Order]:
        for order in self._orders:
            if order.session_id == session_id:
                return order
        return None

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [order for order in self._orders if order.current_status == status]

    def list_all(self) -> list[Order]:
        return list(self._orders)

    def list_orders(self, sort: str = "updated_at_desc", limit: int = 100, offset: int = 0) -> list[Order]:
        orders = list(self._orders)
        if sort == "updated_at_desc":
            orders.sort(key=lambda order: order.updated_at, reverse=True)
        return orders[offset : offset + limit]

    def list_orders_by_status(
        self,
        status: OrderStatus,
        sort: str = "updated_at_desc",
        limit: int = 100,
        offset: int = 0,
    ) -> list[Order]:
        orders = self.find_by_status(status)
        if sort == "updated_at_desc":
            orders.sort(key=lambda order: order.updated_at, reverse=True)
        return orders[offset : offset + limit]

    def save(self, order: Order) -> None:
        for index, existing_order in enumerate(self._orders):
            if existing_order.id == order.id:
                order.updated_at = datetime.now(timezone.utc)
                self._orders[index] = order
                return
        self._orders.append(order)

    def clear(self) -> None:
        self._orders.clear()
