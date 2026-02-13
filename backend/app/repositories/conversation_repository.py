from __future__ import annotations

from typing import Protocol

from app.domain.conversation import Conversation, Message


class ConversationRepository(Protocol):
    def get_or_create(self, order_id: str) -> Conversation:
        ...

    def add_message(self, conversation_id: str, role: str, content: str, metadata: dict[str, object] | None = None) -> Message:
        ...

    def list_messages_for_order(self, order_id: str, limit: int = 100, offset: int = 0) -> list[Message]:
        ...


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._conversations_by_order: dict[str, Conversation] = {}
        self._messages_by_conversation: dict[str, list[Message]] = {}

    def get_or_create(self, order_id: str) -> Conversation:
        conversation = self._conversations_by_order.get(order_id)
        if conversation is None:
            conversation = Conversation.create(order_id=order_id)
            self._conversations_by_order[order_id] = conversation
            self._messages_by_conversation[conversation.id] = []
        return conversation

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> Message:
        message = Message.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata,
        )
        self._messages_by_conversation.setdefault(conversation_id, []).append(message)
        return message

    def list_messages_for_order(self, order_id: str, limit: int = 100, offset: int = 0) -> list[Message]:
        conversation = self._conversations_by_order.get(order_id)
        if conversation is None:
            return []
        messages = sorted(self._messages_by_conversation.get(conversation.id, []), key=lambda m: m.created_at)
        return messages[offset : offset + limit]
