from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.autonomous_agent import AutonomousAgent, DialogueState, RuleBasedValidator


@dataclass
class AutonomousDependencies:
    """Autonomous flow dependencies for orchestration.

    Orchestratorはエージェントの依存関係を受け取り、
    処理順序を明確にするための窓口として振る舞う。
    """

    state: "DialogueState"
    validator: "RuleBasedValidator"


class AutonomousOrchestrator:
    """AutonomousAgentの処理順序をまとめて定義するクラス。

    1. 入力を記録して抽出を実施
    2. 不足項目があれば質問生成へ
    3. 収集完了後に検証
    4. 最終結果 or 追加質問を返す
    """

    def run(
        self,
        agent: "AutonomousAgent",
        deps: AutonomousDependencies,
        message: str,
        base_date: Optional[date],
    ) -> Dict[str, object]:
        # 1. ユーザー入力を記録し、メッセージから情報を抽出する。
        deps.state.record_turn("user", message)
        agent._extract_from_message(message, base_date)

        # 2. 不足項目がある場合は質問生成へ進む。
        if not agent._has_all_fields():
            question = agent._generate_question(message)
            deps.state.record_turn("assistant", question)
            return {"status": "need_more_info", "question": question}

        # 3. 収集した情報を検証し、結果に応じて応答を分岐する。
        is_valid, errors = deps.validator.validate(deps.state)
        if is_valid:
            # 4. 問題がなければ最終出力を返す。
            deps.state.overall_confidence = agent.estimate_overall_confidence(deps.state)
            result = {
                "a_number": deps.state.a_number,
                "work_types": [
                    {"name": wt.name, "confidence": wt.confidence}
                    for wt in deps.state.work_types
                ],
                "date": deps.state.date,
                "date_inferred": deps.state.date_inferred,
                "overall_confidence": deps.state.overall_confidence,
            }
            return {"status": "completed", "result": result}

        # 5. 検証エラーがあれば再質問を行う。
        deps.state.validation_errors = errors
        question = agent._generate_question(message, errors)
        deps.state.record_turn("assistant", question)
        return {"status": "need_more_info", "question": question}
