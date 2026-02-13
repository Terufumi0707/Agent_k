from __future__ import annotations

from app.domain.order import Order, OrderStatus
from app.repositories.order_repository import OrderRepository


class InvalidOrderStatusTransitionError(ValueError):
    pass


class OrderStatusService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def create_new_order(self, order_id: str) -> Order:
        order = Order(id=order_id, current_status=OrderStatus.DELIVERY)
        self._repository.save(order)
        return order

    def confirm_order(self, order_id: str) -> Order:
        order = self._repository.get_by_id(order_id)
        if order is None:
            raise KeyError(order_id)

        if order.current_status != OrderStatus.DELIVERY:
            raise InvalidOrderStatusTransitionError(
                f"invalid transition: {order.current_status} -> {OrderStatus.COORDINATE}"
            )

        order.current_status = OrderStatus.COORDINATE
        self._repository.save(order)
        return order

