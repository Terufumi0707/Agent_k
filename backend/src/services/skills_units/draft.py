from __future__ import annotations

from typing import Any

from src.infrastructure.llm.llm_client import LlmClient
from src.services.skills_units.draft_system_prompt import SYSTEM_PROMPT


class MinutesDraftSkill:
    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        transcript = payload["transcript"]
        if not transcript.strip():
            raise ValueError("transcript is empty")

        prompt = self._build_prompt(
            transcript=transcript,
            num_candidates=min(max(payload.get("candidate_count", 3), 2), 3),
        )

        parsed = self.llm_client.generate_json(prompt)
        if isinstance(parsed, dict):
            return parsed

        raw_response = None
        generate_text = getattr(self.llm_client, "generate_text", None)
        if callable(generate_text):
            raw_response = generate_text(prompt)

        if isinstance(raw_response, str) and raw_response.strip():
            return {"candidates": [{"raw_content": raw_response}]}
        return {"candidates": []}

    def _build_prompt(self, transcript: str, num_candidates: int) -> str:
        return "\n".join(
            [
                SYSTEM_PROMPT,
                "",
                "返却は必ずJSONのみで、次のスキーマに厳密に従ってください。",
                '{"candidates": [{"raw_content": "...", "sections": {"ToDo": ["..."], "決定事項": ["..."]}}]}',
                f"候補数は必ず {num_candidates} 件。",
                "ToDo と 決定事項 は必須。ToDoは必ず担当者と締切日を含める。",
                "raw_content には指定フォーマット(◆TODO/◆決定事項)の本文をそのまま格納。",
                "不足情報は「未確認」と明記し、推測で埋めない。",
                "入力テキスト:",
                transcript,
            ]
        )
