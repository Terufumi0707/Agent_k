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
        self.orders: dict[str, Order] = {}
        self._session_index: dict[str, str] = {}

    def find_by_session_id(self, session_id: str) -> Optional[Order]:
        order_id = self._session_index.get(session_id)
        if order_id is None:
            return None
        return self.orders.get(order_id)

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [order for order in self.orders.values() if order.current_status == status]

    def save(self, order: Order) -> None:
        self.orders[order.id] = order
        self._session_index[order.session_id] = order.id

    def clear(self) -> None:
        self.orders.clear()
        self._session_index.clear()
