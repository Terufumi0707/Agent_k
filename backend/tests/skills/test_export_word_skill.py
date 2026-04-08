from __future__ import annotations

from datetime import datetime

from src.services.skills_units.export_word import MinutesExportWordSkill


def test_export_word_returns_artifact_path_with_date_prefix(tmp_path, monkeypatch):
    skill = MinutesExportWordSkill()

    class FrozenDatetime(datetime):
        @classmethod
        def utcnow(cls):
            return cls(2026, 4, 8)

    monkeypatch.setattr("src.services.skills_units.export_word.datetime", FrozenDatetime)

    result = skill.run(
        {
            "job_id": "job-1",
            "output_dir": str(tmp_path),
            "final_minutes": {"会議概要": "開発定例会議", "決定事項": ["A"]},
        }
    )

    assert result["artifact_path"].endswith("20260408_開発定例会議_A.docx")
