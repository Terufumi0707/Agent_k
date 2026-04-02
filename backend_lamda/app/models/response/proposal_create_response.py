from __future__ import annotations

from pydantic import BaseModel

from app.models.entity.proposal_result import ProposalResult


class ProposalCreateResponse(BaseModel):
    status: str
    message: str
    data: ProposalResult
