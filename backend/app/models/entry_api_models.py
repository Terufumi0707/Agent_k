from __future__ import annotations

from pydantic import BaseModel, Field


class EntryRequest(BaseModel):
    prompt: str = Field(default="", description="CreateEntryOrchestrator にそのまま渡すリクエスト文字列")


class EntryResponse(BaseModel):
    result: str
