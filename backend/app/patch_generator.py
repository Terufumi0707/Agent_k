from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.llm_client import generate_with_system_and_user

PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "patch_generator_agent_system_prompt.txt"
PATCH_AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


class PatchGenerator:
    def __init__(self, system_prompt: str | None = None) -> None:
        self._system_prompt = system_prompt or PATCH_AGENT_SYSTEM_PROMPT

    def generate(self, user_change_input: str, extracted_json: str) -> dict[str, Any]:
        user_prompt = f"user_change_input:\n{user_change_input}\n\nextracted_json:\n{extracted_json}"
        raw_response = generate_with_system_and_user(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
        )
        return self._parse_response(raw_response)

    def _parse_response(self, response: str) -> dict[str, Any]:
        try:
            payload = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return {"patches": []}
        if not isinstance(payload, dict):
            return {"patches": []}
        patches = payload.get("patches")
        if not isinstance(patches, list):
            return {"patches": []}
        return {"patches": patches}
