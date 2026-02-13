from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class Conversation:
    id: str
    order_id: str
    created_at: datetime

    @classmethod
    def create(cls, order_id: str) -> "Conversation":
        return cls(id=str(uuid4()), order_id=order_id, created_at=datetime.now(timezone.utc))


@dataclass
class Message:
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> "Message":
        return cls(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
