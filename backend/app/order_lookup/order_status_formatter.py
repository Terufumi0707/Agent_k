from __future__ import annotations

from pathlib import Path
from typing import Callable

from app.llm_client import generate_with_system_and_user

PROMPT_FILE_PATH = Path(__file__).parent.parent / "prompts" / "order_status_formatter_agent_system_prompt.txt"
ORDER_STATUS_FORMATTER_AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


class OrderStatusFormatter:
    def __init__(
        self,
        llm_client: Callable[[str, str], str] = generate_with_system_and_user,
    ) -> None:
        self._llm_client = llm_client
        self._system_prompt = ORDER_STATUS_FORMATTER_AGENT_SYSTEM_PROMPT

    def format(self, query_result_json: str) -> str:
        user_prompt = f"query_result_json:\n{query_result_json}"
        message = self._llm_client(system_prompt=self._system_prompt, user_prompt=user_prompt)
        if message:
            return message
        return "照会結果の整形に失敗しました。時間をおいて再度お試しください。"
