from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.order import OrderStatus


class EntryRequest(BaseModel):
    prompt: str = Field(default="", description="CreateEntryOrchestrator にそのまま渡すリクエスト文字列")
    session_id: str | None = Field(default=None, description="前回の結果参照に使うセッションID")


class EntryResponse(BaseModel):
    result: str
    session_id: str | None = None


class OrderResponse(BaseModel):
    id: str
    session_id: str
    summary: str
    current_status: OrderStatus
    created_at: datetime
    updated_at: datetime
    n_number: str | None = None
    web_entry_id: str | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: dict[str, Any]
    created_at: datetime
