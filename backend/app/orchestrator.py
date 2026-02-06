from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.llm_client import generate_with_system_and_user

PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "create_entry_agent_system_prompt.txt"
AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
JUDGE_PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "judge_extraction_agent_system_prompt.txt"
JUDGE_AGENT_SYSTEM_PROMPT = JUDGE_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
FORMATTER_PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "user_message_formatter_agent_system_prompt.txt"
FORMATTER_AGENT_SYSTEM_PROMPT = FORMATTER_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


class CreateEntryOrchestrator:
    """create_entry の処理順序を統一するオーケストレーター。"""

    def run(self, prompt: str) -> str:
        extracted_result = generate_with_system_and_user(
            system_prompt=AGENT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        judge_result = self.run_judge(extracted_result)
        return self.build_user_message(extracted_result, judge_result)

    def run_judge(self, prompt: str) -> str:
        """情報抽出JSONの評価を行うJudgeエージェントを実行する。"""

        return generate_with_system_and_user(
            system_prompt=JUDGE_AGENT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

    def build_user_message(self, extracted_result: dict[str, Any] | str, judge_result: dict[str, Any] | str) -> str:
        """抽出結果JSONとJudge結果JSONを入力として、ユーザー表示文を生成する。"""

        extracted_payload = self._to_json_text(extracted_result)
        judge_payload = self._to_json_text(judge_result)
        user_prompt = f"extracted_result:\n{extracted_payload}\n\njudge_result:\n{judge_payload}"

        return generate_with_system_and_user(
            system_prompt=FORMATTER_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    def _to_json_text(self, payload: dict[str, Any] | str) -> str:
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False)
