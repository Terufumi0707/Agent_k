from __future__ import annotations

from dataclasses import asdict
from fastapi import APIRouter

from app.agents.conversation_agent import ConversationAgent
from app.models.entry_api_models import EntryRequest, EntryResponse
from app.repositories.entry_repository import InMemoryEntryRepository
from app.services.entry_service import EntryService
from app.workflows.entry_workflow import EntryWorkflow

router = APIRouter()


_repository = InMemoryEntryRepository()
_service = EntryService(_repository)
_agent = ConversationAgent()
_workflow = EntryWorkflow(_agent, _service)


@router.post("/entries", response_model=EntryResponse)
def create_entry(request: EntryRequest) -> EntryResponse:
    result = _workflow.handle_input(request.payload)
    entry_data = asdict(result.entry) if result.entry else None
    return EntryResponse(
        status=result.status,
        questions=result.questions,
        validation_errors=result.validation_errors,
        entry=entry_data,
    )
