from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.domain.order import OrderStatus
from app.models.entry_api_models import EntryRequest, EntryResponse, OrderResponse
from app.orchestrator import CreateEntryOrchestrator
from app.repositories.order_repository import InMemoryOrderRepository
from app.services.create_entry_stream_service import CreateEntryStreamService

router = APIRouter()
_order_repository = InMemoryOrderRepository()
_orchestrator = CreateEntryOrchestrator(order_repository=_order_repository)
_stream_service = CreateEntryStreamService(orchestrator=_orchestrator)


@router.post("/create_entry", response_model=EntryResponse)
def create_entry(request: EntryRequest) -> EntryResponse:
    result, session_id = _orchestrator.run(request.prompt, session_id=request.session_id)
    return EntryResponse(result=result, session_id=session_id)


@router.post("/create_entry/stream")
def create_entry_stream(request: EntryRequest) -> StreamingResponse:
    return _stream_service.create_stream_response(request)


@router.get("/orders", response_model=list[OrderResponse])
def get_orders(status: OrderStatus) -> list[OrderResponse]:
    orders = _order_repository.find_by_status(status)
    return [
        OrderResponse(id=order.id, session_id=order.session_id, current_status=order.current_status)
        for order in orders
    ]
