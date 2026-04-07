from __future__ import annotations

from unittest.mock import Mock

from src.services.skills_units.draft import MinutesDraftSkill


def test_draft_skill_returns_llm_response_as_is():
    llm_client = Mock()
    llm_client.generate_json.return_value = {
        "candidates": [
            {"raw_content": "A", "sections": {"ToDo": ["t1"], "決定事項": ["d1"]}},
            {"raw_content": "B", "sections": {"ToDo": ["t2"], "決定事項": ["d2"]}},
            {"raw_content": "C", "sections": {"ToDo": ["t3"], "決定事項": ["d3"]}},
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

    assert result == llm_client.generate_json.return_value


def test_draft_skill_returns_empty_candidates_when_llm_returns_none():
    llm_client = Mock()
    llm_client.generate_json.return_value = None
    skill = MinutesDraftSkill(llm_client)

    result = skill.run(
        {
            "transcript": "保田 啓輔: 来週までに要件を整理しましょう。",
            "company_format": {"sections": [{"name": "ToDo", "required": True}]},
            "candidate_count": 2,
        }
    )

    assert result == {"candidates": []}
