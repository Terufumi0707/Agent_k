from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.config import direct_settings


class FasterWhisperTranscriptionService:
    """faster-whisper を利用した最小の文字起こしサービス。"""

    SUPPORTED_EXTENSIONS = {".mp3", ".mp4"}

    def __init__(self) -> None:
        self.model_size = os.getenv("WHISPER_MODEL_SIZE", direct_settings.WHISPER_MODEL_SIZE)
        self.device = os.getenv("WHISPER_DEVICE", direct_settings.WHISPER_DEVICE)
        self.compute_type = os.getenv("WHISPER_COMPUTE_TYPE", direct_settings.WHISPER_COMPUTE_TYPE)
        self._model = None

    def transcribe_audio(self, audio_path: str) -> str:
        target = self._resolve_audio_path(audio_path)
        if target.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("unsupported audio format. only .mp3 and .mp4 are supported")
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(
                "audio file not found: "
                f"{audio_path} (tried: {target}). place the file under server path, e.g. /app/artifacts/*.mp3"
            )

        model = self._get_model()
        try:
            segments, _ = model.transcribe(str(target), beam_size=5)
            transcript = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        except Exception as exc:
            raise RuntimeError(f"failed to transcribe audio: {audio_path}: {exc}") from exc

        if not transcript:
            raise RuntimeError(f"transcription result is empty: {audio_path}")
        return transcript


    def _resolve_audio_path(self, audio_path: str) -> Path:
        target = Path(audio_path)
        if target.is_absolute() or target.exists():
            return target

        project_root = os.getenv("PROJECT_ROOT", "")
        candidates = [Path.cwd() / target]
        if project_root:
            candidates.append(Path(project_root) / "artifacts" / target.name)

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return target

    def _get_model(self):
        if self._model is not None:
            return self._model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "failed to import faster_whisper. "
                "Run `pip install -r backend/requirements.txt` and verify ctranslate2 is available. "
                f"detail: {exc}"
            ) from exc

        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        return self._model


class MinutesTranscribeSkill:
    def __init__(self, transcription_service: FasterWhisperTranscriptionService | None = None) -> None:
        self.transcription_service = transcription_service or FasterWhisperTranscriptionService()

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        audio_path = payload["audio_path"]
        transcript = self.transcription_service.transcribe_audio(audio_path)
        return {"transcript": transcript}
