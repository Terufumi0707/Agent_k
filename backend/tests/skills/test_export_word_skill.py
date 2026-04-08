from __future__ import annotations

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

    assert result["artifact_path"].endswith("job-1.docx")
