from __future__ import annotations

from typing import Any

from src.infrastructure.llm.llm_client import LlmClient


class MinutesService:
    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def create_minutes(self, transcript: str) -> dict[str, Any]:
        prompt = self._build_prompt(transcript)
        generated = self.llm_client.generate_json(prompt)

        if isinstance(generated, dict):
            minutes = str(generated.get("minutes", "")).strip() or transcript
            summary = str(generated.get("summary", "")).strip() or minutes[:200]
            raw_items = generated.get("action_items", [])
            action_items = [str(item).strip() for item in raw_items if str(item).strip()]
            return {
                "minutes": minutes,
                "summary": summary,
                "action_items": action_items,
            }

        return {
            "minutes": transcript,
            "summary": transcript[:200],
            "action_items": [],
        }

    def _build_prompt(self, transcript: str) -> str:
        return (
            "次の会議文字起こしから議事メモを作成してください。"
            "必ずJSONのみで返答し、キーはminutes, summary, action_itemsを使用してください。"
            "action_itemsは文字列配列にしてください。\n\n"
            f"会議文字起こし:\n{transcript}"
        )
