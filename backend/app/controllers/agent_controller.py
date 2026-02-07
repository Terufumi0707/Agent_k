from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.entry_api_models import EntryRequest, EntryResponse
from app.orchestrator import CreateEntryOrchestrator
from app.services.create_entry_stream_service import CreateEntryStreamService

router = APIRouter()
_orchestrator = CreateEntryOrchestrator()
_stream_service = CreateEntryStreamService(orchestrator=_orchestrator)


@router.post("/create_entry", response_model=EntryResponse)
def create_entry(request: EntryRequest) -> EntryResponse:
    result, session_id = _orchestrator.run(request.prompt, session_id=request.session_id)
    return EntryResponse(result=result, session_id=session_id)


@router.post("/create_entry/stream")
def create_entry_stream(request: EntryRequest) -> StreamingResponse:
    return _stream_service.create_stream_response(request)
