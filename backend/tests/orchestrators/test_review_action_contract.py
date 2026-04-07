from __future__ import annotations

import pytest

from src.domain.models import ReviewAction
from src.services.skills_units.review import MinutesReviewSkill


@pytest.fixture
def candidates():
    return [{"会議概要": "案1"}, {"会議概要": "案2"}]


def test_approve_without_instruction_succeeds(candidates):
    skill = MinutesReviewSkill()

    result = skill.run(
        {
            "candidates": candidates,
            "selected_index": 0,
            "action": ReviewAction.APPROVE.value,
            "instruction": None,
        }
    )

    assert result["approved"] is True


def test_revise_requires_instruction(candidates):
    skill = MinutesReviewSkill()

    with pytest.raises(ValueError, match="instruction is required"):
        skill.run(
            {
                "candidates": candidates,
                "selected_index": 0,
                "action": ReviewAction.REVISE.value,
                "instruction": "   ",
            }
        )


def test_approve_is_not_implicitly_interpreted_from_instruction(candidates):
    skill = MinutesReviewSkill()

    with pytest.raises(ValueError, match="unsupported review action"):
        skill.run(
            {
                "candidates": candidates,
                "selected_index": 0,
                "action": "please approve",
                "instruction": "approve",
            }
        )


def test_undefined_action_raises_validation_error(candidates):
    skill = MinutesReviewSkill()

    with pytest.raises(ValueError, match="unsupported review action"):
        skill.run(
            {
                "candidates": candidates,
                "selected_index": 0,
                "action": "unknown",
                "instruction": None,
            }
        )
