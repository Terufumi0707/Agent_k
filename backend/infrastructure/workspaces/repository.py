"""ワークスペース情報を保持するスレッドセーフなインメモリリポジトリ。"""
from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Dict, Iterable, List, Literal, Optional

from ...domain.workspaces import TranscriptEntry, Workspace

DEFAULT_GREETING_MESSAGE = "こんにちは。BayCurrentエージェントです。どの案件から進めますか？"


class WorkspaceNotFoundError(Exception):
    """存在しないワークスペースを操作しようとした際に送出する例外。"""


class WorkspaceRepository:
    """ワークスペースレコードを扱うスレッドセーフなインメモリリポジトリ。"""

    def __init__(self) -> None:
        self._lock = Lock()
        self._workspaces: Dict[str, Workspace] = {}
        self._sequence = 1
        self._bootstrap()

    def _bootstrap(self) -> None:
        """旧フロントエンドの状態を模したモックデータで初期化する。"""

        def create_transcript_entry(
            role: Literal["assistant", "user"],
            content: str,
            offset_seconds: int = 0,
        ) -> TranscriptEntry:
            timestamp = datetime.now(UTC) - timedelta(seconds=offset_seconds)
            return TranscriptEntry(role=role, content=content, timestamp=timestamp)

        now = datetime.now(UTC)
        workspace_seed: List[Workspace] = [
            Workspace(
                id="ws-001",
                title="A社提案準備",
                summary="提案シナリオの素案をエージェントに依頼。資料構成のチェックを進行中。",
                status="running",
                last_updated_at=now,
                transcript=[
                    create_transcript_entry("assistant", DEFAULT_GREETING_MESSAGE, 300),
                    create_transcript_entry(
                        "user",
                        "A社向けの提案資料で、想定課題の整理を手伝ってください。",
                        240,
                    ),
                    create_transcript_entry(
                        "assistant",
                        "承知しました。提案資料の想定課題としては、現状分析、導入メリット、運用体制が焦点となりそうです。",
                        180,
                    ),
                ],
            ),
            Workspace(
                id="ws-002",
                title="A社アポイント準備",
                summary="議事録のたたき台作成を依頼済み。担当者へ共有し完了扱い。",
                status="completed",
                last_updated_at=now - timedelta(hours=1),
                transcript=[
                    create_transcript_entry("assistant", DEFAULT_GREETING_MESSAGE, 3600 + 300),
                    create_transcript_entry(
                        "user",
                        "アポイント後の議事録素案をまとめて。ポイントは簡潔さです。",
                        3600 + 240,
                    ),
                    create_transcript_entry(
                        "assistant",
                        "以下の構成で議事録素案をまとめました。1) 概要 2) 決定事項 3) アクションアイテム。",
                        3600 + 180,
                    ),
                    create_transcript_entry(
                        "user",
                        "ありがとう。担当者に共有したので完了としておいてください。",
                        3600 + 120,
                    ),
                    create_transcript_entry(
                        "assistant",
                        "共有完了しました。必要であれば追って修正案もご用意できます。",
                        3600 + 60,
                    ),
                ],
            ),
        ]

        self._workspaces = {workspace.id: workspace for workspace in workspace_seed}
        self._sequence = len(self._workspaces) + 1

    def list(self) -> List[Workspace]:
        """全ワークスペースレコードのディープコピーを返す。"""

        with self._lock:
            return [deepcopy(workspace) for workspace in self._workspaces.values()]

    def create(self, title: Optional[str] = None) -> Workspace:
        """新しいワークスペースを生成し、レコードのディープコピーを返す。"""

        with self._lock:
            workspace_id = f"ws-{self._sequence:03d}"
            self._sequence += 1
            now = datetime.now(UTC)
            transcript = [
                TranscriptEntry(role="assistant", content=DEFAULT_GREETING_MESSAGE, timestamp=now)
            ]
            workspace = Workspace(
                id=workspace_id,
                title=title or self._build_default_title(len(self._workspaces)),
                summary="",
                status="running",
                last_updated_at=now,
                transcript=transcript,
            )
            self._workspaces[workspace_id] = workspace
            return deepcopy(workspace)

    def update(
        self,
        workspace_id: str,
        *,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[Literal["running", "completed"]] = None,
        transcript: Optional[Iterable[TranscriptEntry]] = None,
        last_updated_at: Optional[datetime] = None,
    ) -> Workspace:
        """ワークスペースを更新し、新しい状態のディープコピーを返す。"""

        with self._lock:
            try:
                workspace = self._workspaces[workspace_id]
            except KeyError as exc:  # pragma: no cover - defensive programming
                raise WorkspaceNotFoundError(workspace_id) from exc

            if title is not None:
                workspace.title = title
            if summary is not None:
                workspace.summary = summary
            if status is not None:
                workspace.status = status
            if transcript is not None:
                workspace.transcript = [deepcopy(entry) for entry in transcript]
            workspace.last_updated_at = last_updated_at or datetime.now(UTC)
            return deepcopy(workspace)

    def delete(self, workspace_id: str) -> None:
        """リポジトリからワークスペースを削除する。"""

        with self._lock:
            if workspace_id not in self._workspaces:
                raise WorkspaceNotFoundError(workspace_id)
            del self._workspaces[workspace_id]

    def _build_default_title(self, count: int) -> str:
        return f"ワークスペース #{count + 1:02d}"


_repository = WorkspaceRepository()


def get_workspace_repository() -> WorkspaceRepository:
    """アプリ全体で共有するシングルトンのリポジトリを返す。"""

    return _repository
