from __future__ import annotations

from app.domain.conversation import Message
from app.domain.order import Order
from app.repositories.conversation_repository import ConversationRepository


class ConversationService:
    def __init__(self, repository: ConversationRepository) -> None:
        self._repository = repository

    def add_order_message(
        self,
        order: Order,
        role: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> Message:
        conversation = self._repository.get_or_create(order_id=order.id)
        return self._repository.add_message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            metadata=metadata,
        )

    def list_order_messages(self, order_id: str, limit: int = 100, offset: int = 0) -> list[Message]:
        return self._repository.list_messages_for_order(order_id=order_id, limit=limit, offset=offset)
