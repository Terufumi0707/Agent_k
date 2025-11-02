"""Vue フロントエンド向けにワークフロー API を提供する FastAPI アプリ。"""
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
    """ユーザー入力からワークフロー候補を推測するためのリクエストボディ。"""

    message: str


class WorkflowCandidate(BaseModel):
    """ユーザーに提示するワークフロー候補のメタデータ。"""

    id: Literal["schedule_change", "other"]
    label: str
    description: str


class SuggestWorkflowResponse(BaseModel):
    """プロンプト分類後に返すレスポンス。候補情報と案内文を含める。"""

    message: str
    candidate: WorkflowCandidate


class WorkflowSelectionRequest(BaseModel):
    """提示したワークフローを採用するか否かの結果を送るリクエストボディ。"""

    message: str
    workflow_id: Literal["schedule_change", "other"]
    decision: Literal["accept", "decline"]


class ChatResponse(BaseModel):
    """ワークフロー実行後にフロントエンドへ返却する応答。"""

    reply: str
    path: list[str]
    classification: str


class TranscriptEntryModel(BaseModel):
    """フロントエンドに返す発話ログの 1 レコードを表すスキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    role: Literal["assistant", "user"]
    content: str
    timestamp: datetime


class WorkspaceModel(BaseModel):
    """API レスポンスで利用するワークスペース情報の構造。"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    summary: str
    status: Literal["running", "completed"]
    last_updated_at: datetime = Field(alias="lastUpdatedAt")
    transcript: list[TranscriptEntryModel]


class WorkspaceCreateRequest(BaseModel):
    """新規ワークスペース作成時のリクエストボディ。"""

    title: Optional[str] = None


class WorkspaceUpdateRequest(BaseModel):
    """ワークスペース情報を更新するときのリクエストボディ。"""

    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[Literal["running", "completed"]] = None
    transcript: Optional[list[TranscriptEntryModel]] = None
    last_updated_at: Optional[datetime] = Field(default=None, alias="lastUpdatedAt")


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    """稼働確認のためのシンプルなエンドポイント。"""

    return {"status": "ok"}


def _validate_prompt(message: str) -> str:
    """共通の入力バリデーションを実施し、整形した文字列を返す。"""

    stripped = message.strip()
    if not stripped:
        raise HTTPException(status_code=422, detail="message must not be empty")
    return stripped


@app.post("/api/workflows/suggest", response_model=SuggestWorkflowResponse)
def suggest_workflow(payload: SuggestWorkflowRequest) -> SuggestWorkflowResponse:
    """ユーザー入力を分類し、実行すべきワークフロー候補を返す。"""

    message = _validate_prompt(payload.message)

    # LLM/正規表現を用いた分類ロジックで入力文を解析する。
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
    """採用決定されたワークフローを実行し、結果を返す。"""

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
        # 日程変更ワークフローを実行し、応答と辿ったパスを取得する。
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
    """ドメインエンティティを API レスポンス用モデルに変換する。"""

    return WorkspaceModel.model_validate(workspace, from_attributes=True)


def _to_transcript_entries(
    entries: list[TranscriptEntryModel] | None,
) -> list[TranscriptEntry] | None:
    """リクエストボディの発話ログをドメインエンティティへ変換する。"""

    if entries is None:
        return None
    return [
        TranscriptEntry(role=item.role, content=item.content, timestamp=item.timestamp)
        for item in entries
    ]


@app.get("/api/workspaces", response_model=list[WorkspaceModel])
def get_workspaces() -> list[WorkspaceModel]:
    """ダッシュボードで表示する全ワークスペース一覧を返す。"""

    workspaces = list_workspaces()
    return [_to_workspace_response(workspace) for workspace in workspaces]


@app.post("/api/workspaces", response_model=WorkspaceModel, status_code=201)
def post_workspace(payload: WorkspaceCreateRequest) -> WorkspaceModel:
    """新規ワークスペースを作成して登録結果を返す。"""

    workspace = create_workspace(payload.title)
    return _to_workspace_response(workspace)


@app.patch("/api/workspaces/{workspace_id}", response_model=WorkspaceModel)
def patch_workspace(
    workspace_id: str, payload: WorkspaceUpdateRequest
) -> WorkspaceModel:
    """リクエスト内容に従ってワークスペース情報を更新する。"""

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
    """リポジトリからワークスペースを削除する。"""

    try:
        delete_workspace(workspace_id)
    except WorkspaceNotFound as exc:  # pragma: no cover - simple mapping
        raise HTTPException(status_code=404, detail="workspace not found") from exc


__all__ = ["app"]
