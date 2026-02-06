from __future__ import annotations

from fastapi import APIRouter

from app.models.entry_api_models import EntryRequest, EntryResponse
from app.orchestrator import CreateEntryOrchestrator

router = APIRouter()
_orchestrator = CreateEntryOrchestrator()


@router.post("/create_entry", response_model=EntryResponse)
def create_entry(request: EntryRequest) -> EntryResponse:
    result, session_id = _orchestrator.run(request.prompt, session_id=request.session_id)
    return EntryResponse(result=result, session_id=session_id)
