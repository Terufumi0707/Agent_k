from __future__ import annotations

from fastapi import APIRouter

from app.models.proposal_api_models import ProposalRequest, ProposalResponse
from app.services.proposal_service import ProposalService

router = APIRouter()
_proposal_service = ProposalService()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent": "proposal-draft"}


@router.post("/proposals", response_model=ProposalResponse)
def create_proposal(request: ProposalRequest) -> ProposalResponse:
    return _proposal_service.create_proposal(request)
