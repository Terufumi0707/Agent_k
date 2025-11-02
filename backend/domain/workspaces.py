"""ワークスペースとその会話履歴を表すドメインモデル群。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


TranscriptRole = Literal["assistant", "user"]


@dataclass
class TranscriptEntry:
    """ワークスペースごとの会話ログを保持するエンティティ。"""

    role: TranscriptRole
    content: str
    timestamp: datetime


@dataclass
class Workspace:
    """バックエンドのアプリケーション層で利用するワークスペースエンティティ。"""

    id: str
    title: str
    summary: str
    status: Literal["running", "completed"]
    last_updated_at: datetime
    transcript: list[TranscriptEntry] = field(default_factory=list)
