from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document

from src.infrastructure.llm.llm_client import LlmClient


class MinutesTranscribeSkill:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        audio_path = payload["audio_path"]
        filename = Path(audio_path).name
        return {"transcript": f"[whisper transcript:{filename}] 会議の要点、決定事項、担当タスク。"}


class MinutesDraftSkill:
    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        candidates = self.llm_client.generate_structured_minutes(
            transcript=payload["transcript"],
            format_definition=payload["company_format"],
            num_candidates=payload.get("candidate_count", 3),
        )
        return {"candidates": candidates}


class MinutesReviewSkill:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        candidates = payload["candidates"]
        selected_index = payload["selected_index"]
        instruction = (payload.get("instruction") or "").strip()
        base = candidates[selected_index]
        if instruction and instruction.lower() != "approve":
            revised = dict(base)
            revised["レビュー反映"] = instruction
            return {"approved": False, "revised_candidate": revised}
        return {"approved": True, "final_minutes": base}


class MinutesExportWordSkill:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload["job_id"]
        output_dir = Path(payload["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{job_id}.docx"

        doc = Document()
        doc.add_heading("議事録", level=0)
        for section, value in payload["final_minutes"].items():
            doc.add_heading(str(section), level=1)
            if isinstance(value, list):
                for item in value:
                    doc.add_paragraph(str(item), style="List Bullet")
            else:
                doc.add_paragraph(str(value))
        doc.save(out_path)
        return {"artifact_path": str(out_path)}
