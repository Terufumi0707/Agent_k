from __future__ import annotations

from pydantic import BaseModel, Field


class ProposalCreateRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=200)
    target_company: str = Field(..., min_length=1, max_length=200)
    background: str = Field(..., min_length=1, max_length=2000)
    issues: str = Field(..., min_length=1, max_length=2000)
    goal: str = Field(..., min_length=1, max_length=1000)
    additional_requirements: str = Field(default="", max_length=2000)
