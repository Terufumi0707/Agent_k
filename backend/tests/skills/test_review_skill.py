from __future__ import annotations

from src.services.skills_units.review import MinutesReviewSkill


def test_review_skill_reflects_selected_candidate():
    skill = MinutesReviewSkill()

    result = skill.run(
        {
            "candidates": [{"会議概要": "候補1"}, {"会議概要": "候補2"}],
            "selected_index": 1,
            "action": "approve",
        }
    )

    assert result["approved"] is True
    assert result["final_minutes"]["会議概要"] == "候補2"
