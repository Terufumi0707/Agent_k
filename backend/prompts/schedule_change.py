"""日程変更ワークフロー向けのプロンプト定義。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduleChangePrompts:
    """LLM 判定に利用するプロンプトをまとめた値オブジェクト。"""

    system: str
    human_template: str


DEFAULT_SCHEDULE_CHANGE_PROMPTS = ScheduleChangePrompts(
    system=(
        "あなたは日程変更リクエストを検知する分類器です。"
        "ユーザーのメッセージが日程変更かどうかを判断してください。"
    ),
    human_template=(
        "次のユーザーメッセージが日程変更を依頼しているか判定してください。"
        "schedule_change もしくは other で回答してください。\n{prompt}"
    ),
)


__all__ = [
    "DEFAULT_SCHEDULE_CHANGE_PROMPTS",
    "ScheduleChangePrompts",
]
