"""Domain models representing workspace records and transcripts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


TranscriptRole = Literal["assistant", "user"]


@dataclass
class TranscriptEntry:
    """Conversation log entry stored for each workspace."""

    role: TranscriptRole
    content: str
    timestamp: datetime


@dataclass
class Workspace:
    """Workspace entity used by the backend application layer."""

    id: str
    title: str
    summary: str
    status: Literal["running", "completed"]
    last_updated_at: datetime
    transcript: list[TranscriptEntry] = field(default_factory=list)
