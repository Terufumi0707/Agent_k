from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.domain.conversation import Conversation, Message

if TYPE_CHECKING:
    from app.domain.order import Order


class ConversationRepository(Protocol):
    def get_or_create(self, order_id: str) -> Conversation:
        ...

    def add_message(self, conversation_id: str, role: str, content: str, metadata: dict[str, object] | None = None) -> Message:
        ...

    def list_messages_for_order(self, order_id: str, limit: int = 100, offset: int = 0) -> list[Message]:
        ...

    def seed_order_histories(self, orders: list[Order]) -> None:
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

    def seed_order_histories(self, orders: list[Order]) -> None:
        for order in orders:
            conversation = self.get_or_create(order_id=order.id)
            if self._messages_by_conversation.get(conversation.id):
                continue

            before_status = "COORDINATE"
            if order.current_status.value == "COORDINATE":
                before_status = "DELIVERY"
            if order.current_status.value == "BACKYARD":
                before_status = "COORDINATE"

            specs: list[dict[str, object]] = [
                {
                    "role": "user",
                    "content": f"{order.id} の進捗と日程調整の状況を確認したいです。",
                    "metadata": {
                        "intent": "CHANGE_REQUEST",
                        "status_event": False,
                        "order_status_before": None,
                        "order_status_after": None,
                    },
                },
                {
                    "role": "assistant",
                    "content": "現在のオーダー情報を確認し、対応方針を案内します。",
                    "metadata": {
                        "intent": "CHANGE_REQUEST",
                        "status_event": False,
                        "order_status_before": None,
                        "order_status_after": None,
                        "tool_call": {"name": "fetch_current_order", "status": "success"},
                    },
                },
                {
                    "role": "assistant",
                    "content": f"最終確認が完了し、ステータスを {order.current_status.value} に更新しました。",
                    "metadata": {
                        "intent": "CONFIRM",
                        "status_event": True,
                        "order_status_before": before_status,
                        "order_status_after": order.current_status.value,
                    },
                },
            ]

            if order.id == "order-delivery-001":
                specs.insert(
                    2,
                    {
                        "role": "user",
                        "content": "連絡先は090-1111-2222です。",
                        "metadata": {
                            "intent": "SUPPLEMENT",
                            "status_event": False,
                            "order_status_before": None,
                            "order_status_after": None,
                        },
                    },
                )
                specs.append(
                    {
                        "role": "system",
                        "content": f"オーダー状態の同期を確認: {order.current_status.value}",
                        "metadata": {
                            "intent": "STATUS_SYNC",
                            "status_event": True,
                            "order_status_before": before_status,
                            "order_status_after": order.current_status.value,
                        },
                    }
                )

            for spec in specs:
                self.add_message(
                    conversation_id=conversation.id,
                    role=str(spec["role"]),
                    content=str(spec["content"]),
                    metadata=dict(spec["metadata"]),
                )
