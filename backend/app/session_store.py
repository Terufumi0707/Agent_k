from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class SessionState:
    """create_entry の処理結果を読み取り専用で保持するセッション状態。"""

    extracted_json: str
    judge_result: str
    user_view_message: str
    intent_result: str
    extracted_json_raw: str | None = None
    pending_patch: str | None = None
    preview_extracted_json: str | None = None


class SessionStore(Protocol):
    def get(self, session_id: str) -> SessionState | None: ...

    def save(self, session_id: str, state: SessionState) -> None: ...


class InMemorySessionStore:
    """将来の永続化差し替えに備えたインメモリ実装。"""

    def __init__(self) -> None:
        self._store: dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState | None:
        return self._store.get(session_id)

    def save(self, session_id: str, state: SessionState) -> None:
        self._store[session_id] = state


def generate_session_id() -> str:
    """外部連携を想定し、文字列のセッションIDを生成する。"""

    return str(uuid4())
