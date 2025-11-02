"""FastAPI application exposing workflow endpoints for the Vue frontend."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from . import WorkflowResult, run_schedule_change_workflow
from .application.workflows.schedule_change import (
    build_schedule_preview,
    classify_schedule_change_prompt,
    extract_schedule_entry_id,
)
from .application.workspaces import (
    WorkspaceNotFound,
    create_workspace,
    delete_workspace,
    list_workspaces,
    update_workspace,
)
from .domain.workspaces import TranscriptEntry, Workspace
from .infrastructure.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="BayCurrent Workflow API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SuggestWorkflowRequest(BaseModel):
    """Payload for requesting a workflow suggestion based on user input."""

    message: str


class WorkflowCandidate(BaseModel):
    """Metadata describing a workflow option suggested to the user."""

    id: Literal["schedule_change", "other"]
    label: str
    description: str


class SuggestWorkflowResponse(BaseModel):
    """Response returned after classifying the prompt into a workflow."""

    message: str
    candidate: WorkflowCandidate


class WorkflowSelectionRequest(BaseModel):
    """Payload sent when the user accepts or declines the proposed workflow."""

    message: str
    workflow_id: Literal["schedule_change", "other"]
    decision: Literal["accept", "decline"]


class ChatResponse(BaseModel):
    """Response returned to the frontend after executing a workflow."""

    reply: str
    path: list[str]
    classification: str


class TranscriptEntryModel(BaseModel):
    """Schema describing a transcript log entry returned to the frontend."""

    model_config = ConfigDict(from_attributes=True)

    role: Literal["assistant", "user"]
    content: str
    timestamp: datetime


class WorkspaceModel(BaseModel):
    """Representation of a workspace used in API responses."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    summary: str
    status: Literal["running", "completed"]
    last_updated_at: datetime = Field(alias="lastUpdatedAt")
    transcript: list[TranscriptEntryModel]


class WorkspaceCreateRequest(BaseModel):
    """Request body for creating a new workspace."""

    title: Optional[str] = None


class WorkspaceUpdateRequest(BaseModel):
    """Request body for updating workspace fields."""

    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[Literal["running", "completed"]] = None
    transcript: Optional[list[TranscriptEntryModel]] = None
    last_updated_at: Optional[datetime] = Field(default=None, alias="lastUpdatedAt")


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    """Simple health-check endpoint."""

    return {"status": "ok"}


def _validate_prompt(message: str) -> str:
    """共通の入力バリデーションを実施し、整形した文字列を返す。"""

    stripped = message.strip()
    if not stripped:
        raise HTTPException(status_code=422, detail="message must not be empty")
    return stripped


@app.post("/api/workflows/suggest", response_model=SuggestWorkflowResponse)
def suggest_workflow(payload: SuggestWorkflowRequest) -> SuggestWorkflowResponse:
    """Classify the user prompt and suggest a workflow to execute."""

    message = _validate_prompt(payload.message)

    classification = classify_schedule_change_prompt(message)
    logger.info(
        "workflow_suggestion classification=%s message=%s", classification, message
    )
    if classification == "schedule_change":
        candidate = WorkflowCandidate(
            id="schedule_change",
            label="日程変更ワークフロー",
            description="社内日程調整システムと連携して予定変更を実施します。",
        )
        reply_lines = ["入力内容から「日程変更」ワークフローが適切と判断しました。"]
        entry_id = extract_schedule_entry_id(message)

        if entry_id:
            preview = build_schedule_preview(entry_id)
            reply_lines.append(preview.message)

            if not preview.found:
                reply_lines.append("現在登録状況を担当チームに確認しながら進めます。")

        reply = "\n".join(reply_lines)
    else:
        candidate = WorkflowCandidate(
            id="other",
            label="その他",
            description="既存の自動化ワークフローでは対応できない内容です。",
        )
        reply = "入力内容は既存のワークフローには該当しませんでした。"

    return SuggestWorkflowResponse(message=reply, candidate=candidate)


@app.post("/api/workflows/select", response_model=ChatResponse)
def select_workflow(payload: WorkflowSelectionRequest) -> ChatResponse:
    """Execute the selected workflow or handle the decline decision."""

    message = _validate_prompt(payload.message)

    if payload.decision == "decline":
        logger.info(
            "workflow_declined workflow_id=%s decision=%s",
            payload.workflow_id,
            payload.decision,
        )
        reply = "別の選択肢は現在ご用意できません。担当者へ引き継ぎます。"
        path = ["classify_intent"]
        classification = "other"
        return ChatResponse(reply=reply, path=path, classification=classification)

    if payload.workflow_id == "schedule_change":
        logger.info(
            "workflow_selected workflow_id=%s decision=%s",
            payload.workflow_id,
            payload.decision,
        )
        result: WorkflowResult = run_schedule_change_workflow(message)
        return ChatResponse(
            reply=result.message,
            path=result.path,
            classification=result.classification,
        )

    logger.info(
        "workflow_fallback workflow_id=%s decision=%s",
        payload.workflow_id,
        payload.decision,
    )
    reply = "今回の内容は手動対応が必要です。担当者に共有しておきます。"
    path = ["classify_intent"]
    classification = "other"
    return ChatResponse(reply=reply, path=path, classification=classification)


def _to_workspace_response(workspace: Workspace) -> WorkspaceModel:
    """Convert a workspace entity to a response model."""

    return WorkspaceModel.model_validate(workspace, from_attributes=True)


def _to_transcript_entries(
    entries: list[TranscriptEntryModel] | None,
) -> list[TranscriptEntry] | None:
    """Convert transcript payload items into domain entities."""

    if entries is None:
        return None
    return [
        TranscriptEntry(role=item.role, content=item.content, timestamp=item.timestamp)
        for item in entries
    ]


@app.get("/api/workspaces", response_model=list[WorkspaceModel])
def get_workspaces() -> list[WorkspaceModel]:
    """Return all available workspaces for the frontend dashboard."""

    workspaces = list_workspaces()
    return [_to_workspace_response(workspace) for workspace in workspaces]


@app.post("/api/workspaces", response_model=WorkspaceModel, status_code=201)
def post_workspace(payload: WorkspaceCreateRequest) -> WorkspaceModel:
    """Create a new workspace and return the persisted record."""

    workspace = create_workspace(payload.title)
    return _to_workspace_response(workspace)


@app.patch("/api/workspaces/{workspace_id}", response_model=WorkspaceModel)
def patch_workspace(
    workspace_id: str, payload: WorkspaceUpdateRequest
) -> WorkspaceModel:
    """Update workspace fields based on the payload."""

    entries = _to_transcript_entries(payload.transcript)
    try:
        workspace = update_workspace(
            workspace_id,
            title=payload.title,
            summary=payload.summary,
            status=payload.status,
            transcript=entries,
            last_updated_at=payload.last_updated_at,
        )
    except WorkspaceNotFound as exc:  # pragma: no cover - simple mapping
        raise HTTPException(status_code=404, detail="workspace not found") from exc
    return _to_workspace_response(workspace)


@app.delete("/api/workspaces/{workspace_id}", status_code=204)
def delete_workspace_record(workspace_id: str) -> None:
    """Remove a workspace from the repository."""

    try:
        delete_workspace(workspace_id)
    except WorkspaceNotFound as exc:  # pragma: no cover - simple mapping
        raise HTTPException(status_code=404, detail="workspace not found") from exc


__all__ = ["app"]
