from __future__ import annotations

from pydantic import BaseModel, Field


class EntryRequest(BaseModel):
    payload: str = Field(default="", description="自然言語の入力内容")


class EntryResponse(BaseModel):
    status: str
    questions: list[str]
    validation_errors: list[dict[str, str]]
    entry: dict | None
