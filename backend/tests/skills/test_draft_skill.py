from __future__ import annotations

from unittest.mock import Mock

from src.services.skills_units.draft import MinutesDraftSkill


def test_draft_skill_returns_requested_candidate_count():
    llm_client = Mock()
    llm_client.generate_json.return_value = {
        "candidates": [
            {"会議概要": "A"},
            {"会議概要": "B"},
            {"会議概要": "C"},
        ]
    }
    skill = MinutesDraftSkill(llm_client)

    result = skill.run(
        {
            "transcript": "会議内容",
            "company_format": {"sections": [{"name": "会議概要", "required": True}]},
            "candidate_count": 3,
        }
    )

    assert len(result["candidates"]) == 3
