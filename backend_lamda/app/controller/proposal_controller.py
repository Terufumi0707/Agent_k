from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.request.proposal_create_request import ProposalCreateRequest
from app.models.response.proposal_create_response import ProposalCreateResponse
from app.orchestrator.proposal_orchestrator import ProposalOrchestrator
from app.providers import get_proposal_orchestrator

router = APIRouter(prefix="/proposal", tags=["proposal"])


@router.post("/create", response_model=ProposalCreateResponse)
async def create_proposal(
    request: ProposalCreateRequest,
    orchestrator: ProposalOrchestrator = Depends(get_proposal_orchestrator),
) -> ProposalCreateResponse:
    return await orchestrator.create_proposal(request)
