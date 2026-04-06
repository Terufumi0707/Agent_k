from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document

from src.infrastructure.llm.llm_client import LlmClient


class MinutesTranscribeSkill:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        # 実運用では音声認識結果を返す想定。現在はファイル名を含むダミー文字列を返す。
        audio_path = payload["audio_path"]
        filename = Path(audio_path).name
        return {"transcript": f"[whisper transcript:{filename}] 会議の要点、決定事項、担当タスク。"}


class MinutesDraftSkill:
    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        # 文字起こし結果と社内フォーマットを使って、複数の候補案を生成する。
        candidates = self.llm_client.generate_structured_minutes(
            transcript=payload["transcript"],
            format_definition=payload["company_format"],
            num_candidates=payload.get("candidate_count", 3),
        )
        return {"candidates": candidates}


class MinutesReviewSkill:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        # レビュー対象の候補と指示内容を受け取り、承認/差し戻しを判定する。
        candidates = payload["candidates"]
        selected_index = payload["selected_index"]
        instruction = (payload.get("instruction") or "").strip()
        base = candidates[selected_index]
        if instruction and instruction.lower() != "approve":
            # 差し戻し時は元候補をコピーし、レビュー内容を追記した改訂版を返す。
            revised = dict(base)
            revised["レビュー反映"] = instruction
            return {"approved": False, "revised_candidate": revised}
        return {"approved": True, "final_minutes": base}


class MinutesExportWordSkill:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        # 最終確定した議事録データを Word 形式で保存する。
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
