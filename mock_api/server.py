"""FastAPI application exposing the mock API endpoints used in development."""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from backend.domain.schedule_change.entities import ScheduleChangeRequest

from .mock_backend_chat import mock_reply
from .schedule_change_service import handle_schedule_change_request


class ChatRequest(BaseModel):
    """Request payload for the chat mock endpoint."""

    message: str


class ChatResponse(BaseModel):
    """Response payload returned from the chat mock endpoint."""

    reply: str


class ScheduleChangePayload(BaseModel):
    """Request payload accepted by the schedule change mock endpoint."""

    entry_id: str
    prompt: str
    requester: Optional[str] = None
    reason: Optional[str] = None


class ScheduleChangeResult(BaseModel):
    """Response payload produced by the schedule change mock endpoint."""

    status: str
    message: str


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    app = FastAPI(title="Mock Backend API", version="0.1.0")

    @app.get("/healthz")
    def healthcheck() -> dict[str, str]:
        """Simple health-check endpoint for readiness probes."""

        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(payload: ChatRequest) -> ChatResponse:
        """Echo back a deterministic reply for UI development."""

        return ChatResponse(reply=mock_reply(payload.message))

    @app.post("/schedule-change", response_model=ScheduleChangeResult)
    def schedule_change(payload: ScheduleChangePayload) -> ScheduleChangeResult:
        """Forward schedule change requests to the deterministic mock service."""

        request = ScheduleChangeRequest(
            entry_id=payload.entry_id,
            prompt=payload.prompt,
            requester=payload.requester,
            reason=payload.reason,
        )
        response = handle_schedule_change_request(request)
        return ScheduleChangeResult(status=response.status, message=response.message)

    return app


app = create_app()


__all__ = [
    "ChatRequest",
    "ChatResponse",
    "ScheduleChangePayload",
    "ScheduleChangeResult",
    "app",
    "create_app",
]
