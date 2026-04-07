from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document


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
