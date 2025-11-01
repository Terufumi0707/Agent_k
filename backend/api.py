"""FastAPI application exposing workflow endpoints for the Vue frontend."""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import WorkflowResult, run_schedule_change_workflow
from .application.workflows.schedule_change import classify_schedule_change_prompt
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
        reply = "入力内容から「日程変更」ワークフローが適切と判断しました。"
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


__all__ = ["app"]
