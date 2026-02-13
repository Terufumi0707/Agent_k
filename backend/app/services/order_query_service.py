from __future__ import annotations

from app.domain.order import Order, OrderStatus
from app.domain.conversation import Message
from app.models.entry_api_models import MessageResponse, OrderResponse, OrderStatusGroupResponse
from app.services.conversation_service import ConversationService
from app.services.order_service import OrderService


class OrderQueryService:
    def __init__(self, order_service: OrderService, conversation_service: ConversationService) -> None:
        self._order_service = order_service
        self._conversation_service = conversation_service

    def get_orders(self, limit: int = 100, offset: int = 0, sort: str = "updated_at_desc") -> list[OrderResponse]:
        if sort != "updated_at_desc":
            return []
        orders = self._order_service.list_orders(limit=limit, offset=offset)
        return [self._to_order_response(order) for order in orders]

    def get_orders_legacy(self, status: OrderStatus | None = None) -> list[OrderResponse]:
        orders = self._order_service.list_orders_legacy(status=status)
        return [self._to_order_response(order) for order in orders]

    def get_order_status_groups(self, limit: int = 100, offset: int = 0) -> list[OrderStatusGroupResponse]:
        groups = self._order_service.list_orders_by_status_group(limit=limit, offset=offset)
        return [
            OrderStatusGroupResponse(
                status=group["status"],
                orders=[self._to_order_response(order) for order in group["orders"]],
            )
            for group in groups
        ]

    def get_order_messages(self, order_id: str, limit: int = 100, offset: int = 0) -> list[MessageResponse]:
        messages = self._conversation_service.list_order_messages(order_id=order_id, limit=limit, offset=offset)
        return [self._to_message_response(message) for message in messages]

    def _to_order_response(self, order: Order) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            session_id=order.session_id,
            summary=order.summary,
            current_status=order.current_status,
            created_at=order.created_at,
            updated_at=order.updated_at,
            n_number=order.n_number,
            web_entry_id=order.web_entry_id,
        )

    def _to_message_response(self, message: Message) -> MessageResponse:
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
            created_at=message.created_at,
        )
