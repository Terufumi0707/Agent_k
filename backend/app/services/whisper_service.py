from __future__ import annotations

from pathlib import Path


class WhisperService:
    """Whisper interface stub. Replace with real SDK call in production."""

    def transcribe(self, audio_path: str) -> str:
        filename = Path(audio_path).name
        return f"[transcript from {filename}] 商談内容の仮文字起こしです。要件、決定事項、ToDoが含まれます。"
