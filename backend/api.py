"""FastAPI application exposing workflow endpoints for the Vue frontend."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import WorkflowResult, run_schedule_change_workflow

app = FastAPI(title="BayCurrent Workflow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Payload for a chat message sent from the frontend."""

    message: str


class ChatResponse(BaseModel):
    """Response returned to the frontend after running the workflow."""

    reply: str
    path: list[str]
    classification: str


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    """Simple health-check endpoint."""

    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Execute the schedule change workflow and return its result."""

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="message must not be empty")

    result: WorkflowResult = run_schedule_change_workflow(message)

    return ChatResponse(
        reply=result.message,
        path=result.path,
        classification=result.classification,
    )


__all__ = ["app"]
