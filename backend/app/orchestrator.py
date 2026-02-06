from __future__ import annotations

from pathlib import Path

from app.llm_client import generate_with_system_and_user

PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "create_entry_agent_system_prompt.txt"
AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
JUDGE_PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "judge_extraction_agent_system_prompt.txt"
JUDGE_AGENT_SYSTEM_PROMPT = JUDGE_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


class CreateEntryOrchestrator:
    """create_entry の処理順序を統一するオーケストレーター。"""

    def run(self, prompt: str) -> str:
        return generate_with_system_and_user(
            system_prompt=AGENT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

    def run_judge(self, prompt: str) -> str:
        """情報抽出JSONの評価を行うJudgeエージェントを実行する。"""

        return generate_with_system_and_user(
            system_prompt=JUDGE_AGENT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
