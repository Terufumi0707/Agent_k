"""ワークスペースの CRUD 処理を提供するアプリケーションサービス。"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Literal, Optional

from ...domain.workspaces import TranscriptEntry, Workspace
from ...infrastructure.workspaces import (
    WorkspaceNotFoundError,
    get_workspace_repository,
)


class WorkspaceServiceError(Exception):
    """ワークスペースサービスで発生し得る例外の基底クラス。"""


class WorkspaceNotFound(WorkspaceServiceError):
    """対象のワークスペースが存在しない場合に送出する例外。"""


def list_workspaces() -> list[Workspace]:
    """リポジトリに登録されているすべてのワークスペースを取得する。"""

    repository = get_workspace_repository()
    return repository.list()


def create_workspace(title: Optional[str] = None) -> Workspace:
    """新しいワークスペースを作成し、生成されたエンティティを返す。"""

    repository = get_workspace_repository()
    return repository.create(title)


def update_workspace(
    workspace_id: str,
    *,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    status: Optional[Literal["running", "completed"]] = None,
    transcript: Optional[Iterable[TranscriptEntry]] = None,
    last_updated_at: Optional[datetime] = None,
) -> Workspace:
    """リポジトリ層へ処理を委譲してワークスペースの各項目を更新する。"""

    repository = get_workspace_repository()
    try:
        return repository.update(
            workspace_id,
            title=title,
            summary=summary,
            status=status,
            transcript=transcript,
            last_updated_at=last_updated_at,
        )
    except WorkspaceNotFoundError as exc:  # pragma: no cover - thin wrapper
        raise WorkspaceNotFound(workspace_id) from exc


def delete_workspace(workspace_id: str) -> None:
    """リポジトリから指定 ID のワークスペースを削除する。"""

    repository = get_workspace_repository()
    try:
        repository.delete(workspace_id)
    except WorkspaceNotFoundError as exc:  # pragma: no cover - thin wrapper
        raise WorkspaceNotFound(workspace_id) from exc
