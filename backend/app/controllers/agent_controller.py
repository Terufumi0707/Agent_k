from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.entry_api_models import EntryRequest, EntryResponse, MessageResponse, OrderResponse, OrderStatusGroupResponse
from app.orchestrator import CreateEntryOrchestrator
from app.repositories.conversation_repository import InMemoryConversationRepository
from app.repositories.order_repository import InMemoryOrderRepository
from app.services.conversation_service import ConversationService
from app.services.create_entry_stream_service import CreateEntryStreamService
from app.services.order_query_service import OrderQueryService
from app.services.order_service import OrderService
from app.domain.order import OrderStatus

router = APIRouter()
_order_repository = InMemoryOrderRepository()
_conversation_repository = InMemoryConversationRepository()
_order_service = OrderService(repository=_order_repository)
_conversation_service = ConversationService(repository=_conversation_repository)
_conversation_service.seed_order_histories(_order_repository.list_all())
_order_query_service = OrderQueryService(
    order_service=_order_service,
    conversation_service=_conversation_service,
)
_orchestrator = CreateEntryOrchestrator(
    order_repository=_order_repository,
    order_service=_order_service,
    conversation_repository=_conversation_repository,
    conversation_service=_conversation_service,
)
_stream_service = CreateEntryStreamService(orchestrator=_orchestrator)


@router.post("/create_entry", response_model=EntryResponse)
async def create_entry(request: EntryRequest) -> EntryResponse:
    result, session_id = await _orchestrator.run(request.prompt, session_id=request.session_id)
    return EntryResponse(result=result, session_id=session_id)


@router.post("/create_entry/stream")
def create_entry_stream(request: EntryRequest) -> StreamingResponse:
    return _stream_service.create_stream_response(request)


@router.get("/v1/orders", response_model=list[OrderResponse])
def get_orders(limit: int = 100, offset: int = 0, sort: str = "updated_at_desc") -> list[OrderResponse]:
    return _order_query_service.get_orders(limit=limit, offset=offset, sort=sort)


@router.get("/orders", response_model=list[OrderResponse])
def get_orders_legacy(status: OrderStatus | None = None) -> list[OrderResponse]:
    return _order_query_service.get_orders_legacy(status=status)


@router.get("/v1/orders/status-groups", response_model=list[OrderStatusGroupResponse])
def get_order_status_groups(limit: int = 100, offset: int = 0) -> list[OrderStatusGroupResponse]:
    return _order_query_service.get_order_status_groups(limit=limit, offset=offset)


@router.get("/v1/orders/{order_id}/messages", response_model=list[MessageResponse])
def get_order_messages(order_id: str, limit: int = 100, offset: int = 0) -> list[MessageResponse]:
    return _order_query_service.get_order_messages(order_id=order_id, limit=limit, offset=offset)
