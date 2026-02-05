from __future__ import annotations

from fastapi import APIRouter

from app.models.entry_api_models import EntryRequest, EntryResponse
from app.orchestrator import CreateEntryOrchestrator

router = APIRouter()
_orchestrator = CreateEntryOrchestrator()


@router.post("/create_entry", response_model=EntryResponse)
def create_entry(request: EntryRequest) -> EntryResponse:
    result = _orchestrator.run(request.prompt)
    return EntryResponse(result=result)
