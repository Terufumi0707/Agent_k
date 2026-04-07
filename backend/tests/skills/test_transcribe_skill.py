from __future__ import annotations

from src.services.skills_units.transcribe import MinutesTranscribeSkill


def test_transcribe_returns_transcript_with_filename():
    skill = MinutesTranscribeSkill()

    result = skill.run({"audio_path": "/tmp/meeting.wav"})

    assert "meeting.wav" in result["transcript"]
