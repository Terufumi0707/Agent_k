from __future__ import annotations

from typing import Any

from src.infrastructure.llm.llm_client import LlmClient


class MinutesGenerationService:
    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def generate_candidates(
        self,
        transcript: str,
        format_definition: dict[str, Any],
        num_candidates: int = 3,
    ) -> list[dict[str, Any]]:
        drafts = self.llm_client.generate_structured_minutes(
            transcript=transcript,
            format_definition=format_definition,
            num_candidates=num_candidates,
        )
        self._validate_required_sections(drafts, format_definition)
        return drafts

    def revise_candidate(
        self,
        transcript: str,
        format_definition: dict[str, Any],
        base_draft: dict[str, Any],
        feedback_text: str,
    ) -> dict[str, Any]:
        revised = self.llm_client.generate_structured_minutes(
            transcript=transcript,
            format_definition=format_definition,
            num_candidates=1,
            feedback=feedback_text,
            base_draft=base_draft,
        )[0]
        self._validate_required_sections([revised], format_definition)
        return revised

    def _validate_required_sections(self, drafts: list[dict[str, Any]], format_definition: dict[str, Any]) -> None:
        required = [s["name"] for s in format_definition["sections"] if s.get("required", False)]
        for idx, draft in enumerate(drafts, start=1):
            missing = [name for name in required if name not in draft or not draft[name]]
            if missing:
                raise ValueError(f"Draft {idx} missing required sections: {missing}")
