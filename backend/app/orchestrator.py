from __future__ import annotations

from pathlib import Path

from app.llm_client import generate_with_system_and_user

PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "create_entry_agent_system_prompt.txt"
AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


class CreateEntryOrchestrator:
    """create_entry の処理順序を統一するオーケストレーター。"""

    def run(self, prompt: str) -> str:
        return generate_with_system_and_user(
            system_prompt=AGENT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
