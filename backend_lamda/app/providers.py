from __future__ import annotations

from app.client.gas_client import GasClient
from app.client.gemini_client import GeminiClient
from app.client.looker_client import LookerClient
from app.config.settings import get_settings
from app.orchestrator.proposal_orchestrator import ProposalOrchestrator
from app.service.proposal_service import ProposalService


def get_proposal_orchestrator() -> ProposalOrchestrator:
    settings = get_settings()
    looker_client = LookerClient(
        base_url=settings.looker_api_base_url,
        api_key=settings.looker_api_key,
        timeout_seconds=settings.http_timeout_seconds,
        use_stub=settings.use_stub_clients,
    )
    gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.http_timeout_seconds,
        use_stub=settings.use_stub_clients,
    )
    gas_client = GasClient(
        base_url=settings.gas_api_base_url,
        api_key=settings.gas_api_key,
        timeout_seconds=settings.http_timeout_seconds,
        use_stub=settings.use_stub_clients,
    )

    service = ProposalService(
        looker_client=looker_client,
        gemini_client=gemini_client,
        gas_client=gas_client,
    )
    return ProposalOrchestrator(proposal_service=service)
