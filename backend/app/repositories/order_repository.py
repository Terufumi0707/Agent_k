from __future__ import annotations

from typing import Protocol

from app.domain.order import Order


class OrderRepository(Protocol):
    def get_by_id(self, order_id: str) -> Order | None:
        ...

    def save(self, order: Order) -> None:
        ...


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    def get_by_id(self, order_id: str) -> Order | None:
        return self._store.get(order_id)

    def save(self, order: Order) -> None:
        self._store[order.id] = order

