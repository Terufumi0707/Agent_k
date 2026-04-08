from __future__ import annotations

from pathlib import Path

import pytest

from src.services.skills_units.transcribe import (
    FasterWhisperTranscriptionService,
    MinutesTranscribeSkill,
)


class DummyTranscriptionService:
    def __init__(self, transcript: str = "テスト文字起こし") -> None:
        self.transcript = transcript

    def transcribe_audio(self, audio_path: str) -> str:
        return f"{self.transcript}:{Path(audio_path).name}"


def test_transcribe_returns_transcript_text_from_service():
    skill = MinutesTranscribeSkill(transcription_service=DummyTranscriptionService())

    result = skill.run({"audio_path": "/tmp/meeting.mp3"})

    assert result["transcript"] == "テスト文字起こし:meeting.mp3"


def test_transcribe_requires_audio_path():
    skill = MinutesTranscribeSkill(transcription_service=DummyTranscriptionService())

    with pytest.raises(KeyError):
        skill.run({})


def test_transcription_service_rejects_non_mp3_mp4():
    service = FasterWhisperTranscriptionService()

    with pytest.raises(ValueError, match="only .mp3 and .mp4"):
        service.transcribe_audio("/tmp/meeting.wav")
