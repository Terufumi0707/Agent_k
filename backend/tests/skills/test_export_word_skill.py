from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.services.skills_units.export_word import MinutesExportWordSkill


def test_export_word_returns_artifact_path(tmp_path):
    skill = MinutesExportWordSkill()

    result = skill.run(
        {
            "job_id": "job-1",
            "output_dir": str(tmp_path),
            "final_minutes": {"会議概要": "内容", "決定事項": ["A"]},
        }
    )

    artifact_name = Path(result["artifact_path"]).name
    assert artifact_name.endswith(".docx")
    assert artifact_name.startswith(datetime.now().strftime("%Y%m%d_"))
    assert "内容" in artifact_name
