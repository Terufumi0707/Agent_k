from __future__ import annotations

from pydantic import BaseModel, Field


class EntryRequest(BaseModel):
    entry_id: str | None = Field(default=None, description="Aナンバー")
    payload: list[dict] = Field(default_factory=list)


class EntryResponse(BaseModel):
    status: str
    questions: list[str]
    validation_errors: list[dict[str, str]]
    entry: dict | None
