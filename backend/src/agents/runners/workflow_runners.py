from __future__ import annotations

from pathlib import Path
from typing import Any

from src.services.export_service import DocxExporter
from src.services.minutes_generation_service import MinutesGenerationService
from src.services.whisper_service import WhisperService


class WhisperRunner:
    def __init__(self, whisper_service: WhisperService) -> None:
        self.whisper_service = whisper_service

    def run(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        return {"transcript": self.whisper_service.transcribe(input_payload["audio_path"])}


class DraftGenerationRunner:
    def __init__(self, minutes_service: MinutesGenerationService) -> None:
        self.minutes_service = minutes_service

    def run(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        drafts = self.minutes_service.generate_candidates(
            transcript=input_payload["transcript"],
            format_definition=input_payload["format_definition"],
            num_candidates=input_payload.get("num_candidates", 3),
        )
        return {"candidates": drafts}


class RevisionRunner:
    def __init__(self, minutes_service: MinutesGenerationService) -> None:
        self.minutes_service = minutes_service

    def run(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        revised = self.minutes_service.revise_candidate(
            transcript=input_payload["transcript"],
            format_definition=input_payload["format_definition"],
            base_draft=input_payload["base_draft"],
            feedback_text=input_payload["feedback_text"],
        )
        return {"revised_candidate": revised}


class ExportRunner:
    def __init__(self, exporter: DocxExporter, output_dir: Path) -> None:
        self.exporter = exporter
        self.output_dir = output_dir

    def run(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        path = self.exporter.export(
            job_id=input_payload["job_id"],
            structured_minutes=input_payload["final_minutes"],
            output_dir=self.output_dir,
        )
        return {"artifact_path": str(path)}
