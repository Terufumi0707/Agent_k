from __future__ import annotations

from pydantic import BaseModel, Field


class ProposalRequest(BaseModel):
    """Request payload for proposal generation."""

    theme: str = Field(..., min_length=1, description="提案書のテーマ")
    objective: str = Field(..., min_length=1, description="提案の目的")
    constraints: list[str] = Field(default_factory=list, description="前提条件・制約")
    audience: str | None = Field(default=None, description="想定読者")


class ProposalResponse(BaseModel):
    """Response payload with generated proposal draft."""

    title: str
    summary: str
    sections: list[str]
