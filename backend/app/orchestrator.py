from __future__ import annotations

from app.llm_client import generate_raw_text


class CreateEntryOrchestrator:
    """create_entry の処理順序を統一するオーケストレーター。"""

    def run(self, prompt: str) -> str:
        return generate_raw_text(prompt)
