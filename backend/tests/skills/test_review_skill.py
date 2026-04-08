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


def test_review_skill_revise_can_attach_past_minutes_reference_and_structured_logs():
    skill = MinutesReviewSkill()

    result = skill.run(
        {
            "candidates": [
                {"sections": {"会議概要": "候補1", "ToDo": ["A"]}},
                {"sections": {"会議概要": "候補2", "ToDo": ["B"]}},
            ],
            "selected_index": 1,
            "action": "revise",
            "instruction": "過去の議事メモも参照して、会話ログも構造化して残しておいて",
            "transcript": "田中: 進捗を共有します\n佐藤：レビューをお願いします",
            "review_comments": ["前回の差し戻しコメント"],
        }
    )

    assert result["approved"] is False
    revised = result["revised_candidate"]["sections"]
    assert "参照した過去議事メモ" in revised
    assert revised["参照した過去議事メモ"][0]["candidate_index"] == 0
    assert revised["構造化会話ログ"][0]["speaker"] == "田中"
    assert revised["構造化会話ログ"][1]["speaker"] == "佐藤"
    assert revised["レビュー履歴"] == ["前回の差し戻しコメント"]
