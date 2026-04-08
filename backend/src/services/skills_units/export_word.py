from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document

from src.infrastructure.llm.llm_client import LlmClient


class MinutesExportWordSkill:
    def __init__(self, llm_client: LlmClient | None = None) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        # 最終確定した議事録データを Word 形式で保存する。
        output_dir = Path(payload["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        final_minutes = payload["final_minutes"]
        date_prefix = datetime.utcnow().strftime("%Y%m%d")
        summary_name = self._generate_summary_name(final_minutes)
        out_path = output_dir / f"{date_prefix}_{summary_name}.docx"

        doc = Document()
        doc.add_heading("議事録", level=0)
        for section, value in final_minutes.items():
            doc.add_heading(str(section), level=1)
            if isinstance(value, list):
                for item in value:
                    doc.add_paragraph(str(item), style="List Bullet")
            else:
                doc.add_paragraph(str(value))
        doc.save(out_path)
        return {"artifact_path": str(out_path)}

    def _generate_summary_name(self, final_minutes: dict[str, Any]) -> str:
        llm_name = self._generate_summary_name_with_llm(final_minutes)
        if llm_name:
            return llm_name

        # フォールバック: 冒頭テキストからファイル名を生成する。
        fallback_source = "_".join(str(v) for v in final_minutes.values() if v)
        sanitized = self._sanitize_filename_segment(fallback_source)
        return sanitized[:40] if sanitized else "会議メモ"

    def _generate_summary_name_with_llm(self, final_minutes: dict[str, Any]) -> str | None:
        llm_client = self.llm_client or LlmClient()

        prompt = (
            "以下の議事録内容を要約し、ファイル名に使える会議名を日本語で1つ返してください。"
            "JSONのみで返し、キーはname。"
            "英数字と日本語、ハイフン、アンダースコア以外は使わないでください。\n\n"
            f"議事録: {final_minutes}"
        )
        generated = llm_client.generate_json(prompt)
        if not isinstance(generated, dict):
            return None

        name = self._sanitize_filename_segment(str(generated.get("name", "")))
        if not name:
            return None
        return name[:40]

    def _sanitize_filename_segment(self, name: str) -> str:
        normalized = re.sub(r"\s+", "_", name.strip())
        sanitized = re.sub(r"[^0-9A-Za-zぁ-んァ-ン一-龥々ー_-]", "", normalized)
        return sanitized.strip("._-")
