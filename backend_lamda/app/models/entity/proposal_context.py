from __future__ import annotations

from pydantic import BaseModel


class ProposalContext(BaseModel):
    theme: str
    target_company: str
    background: str
    issues: str
    goal: str
    additional_requirements: str
