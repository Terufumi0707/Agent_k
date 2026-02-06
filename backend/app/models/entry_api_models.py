from __future__ import annotations

from pydantic import BaseModel, Field


class EntryRequest(BaseModel):
    prompt: str = Field(default="", description="CreateEntryOrchestrator にそのまま渡すリクエスト文字列")
    session_id: str | None = Field(default=None, description="前回の結果参照に使うセッションID")


class EntryResponse(BaseModel):
    result: str
    session_id: str | None = None
