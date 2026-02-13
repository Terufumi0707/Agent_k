from __future__ import annotations

from typing import Optional, Protocol

from app.domain.order import Order, OrderStatus


class OrderRepository(Protocol):
    def find_by_session_id(self, session_id: str) -> Optional[Order]:
        ...

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        ...

    def save(self, order: Order) -> None:
        ...


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders = [
            Order(id="order-delivery-001", session_id="session-delivery-001", current_status=OrderStatus.DELIVERY),
            Order(id="order-delivery-002", session_id="session-delivery-002", current_status=OrderStatus.DELIVERY),
            Order(id="order-delivery-003", session_id="session-delivery-003", current_status=OrderStatus.DELIVERY),
            Order(
                id="order-coordinate-001",
                session_id="session-coordinate-001",
                current_status=OrderStatus.COORDINATE,
            ),
            Order(
                id="order-coordinate-002",
                session_id="session-coordinate-002",
                current_status=OrderStatus.COORDINATE,
            ),
            Order(
                id="order-coordinate-003",
                session_id="session-coordinate-003",
                current_status=OrderStatus.COORDINATE,
            ),
            Order(id="order-backyard-001", session_id="session-backyard-001", current_status=OrderStatus.BACKYARD),
            Order(id="order-backyard-002", session_id="session-backyard-002", current_status=OrderStatus.BACKYARD),
            Order(id="order-backyard-003", session_id="session-backyard-003", current_status=OrderStatus.BACKYARD),
        ]

    def find_by_session_id(self, session_id: str) -> Optional[Order]:
        for order in self._orders:
            if order.session_id == session_id:
                return order
        return None

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [order for order in self._orders if order.current_status == status]

    def save(self, order: Order) -> None:
        for index, existing_order in enumerate(self._orders):
            if existing_order.id == order.id:
                self._orders[index] = order
                return
        self._orders.append(order)

    def clear(self) -> None:
        self._orders.clear()
