from __future__ import annotations

from app.domain.order import Order, OrderStatus
from app.repositories.order_repository import OrderRepository


class InvalidOrderStatusTransitionError(ValueError):
    pass


class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def create_if_not_exists(self, session_id: str) -> Order:
        existing_order = self._repository.find_by_session_id(session_id)
        if existing_order is not None:
            return existing_order

        order = Order.create(session_id=session_id, current_status=OrderStatus.DELIVERY)
        self._repository.save(order)
        return order

    def move_to_coordinate(self, session_id: str) -> None:
        order = self._repository.find_by_session_id(session_id)
        if order is None:
            raise KeyError(session_id)

        if order.current_status != OrderStatus.DELIVERY:
            raise InvalidOrderStatusTransitionError(
                f"invalid transition: {order.current_status} -> {OrderStatus.COORDINATE}"
            )

        order.current_status = OrderStatus.COORDINATE
        self._repository.save(order)

    def move_to_backyard(self, session_id: str) -> None:
        order = self._repository.find_by_session_id(session_id)
        if order is None:
            raise KeyError(session_id)

        order.current_status = OrderStatus.BACKYARD
        self._repository.save(order)
