from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from app.llm_client import generate_with_system_and_user
from app.session_store import SessionState

PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "intent_classifier_agent_system_prompt.txt"
INTENT_AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


@dataclass(frozen=True)
class IntentClassification:
    intent: str
    confidence: float
    reason: str


class IntentClassifier:
    def __init__(self) -> None:
        self._system_prompt = INTENT_AGENT_SYSTEM_PROMPT

    def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
        summary = self._build_session_summary(session_state)
        user_prompt = f"latest_input:\n{user_input}\n\nsession_summary:\n{summary}"
        raw_response = generate_with_system_and_user(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
        )
        return self._parse_response(raw_response)

    def _build_session_summary(self, session_state: SessionState | None) -> str:
        if session_state is None:
            return "null"
        payload = {
            "extracted_json": session_state.extracted_json,
            "judge_result": session_state.judge_result,
            "user_view_message": session_state.user_view_message,
            "intent_result": session_state.intent_result,
        }
        return json.dumps(payload, ensure_ascii=False)

    def _parse_response(self, response: str) -> IntentClassification:
        try:
            payload = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return IntentClassification(
                intent="UNKNOWN",
                confidence=0.0,
                reason="LLM response was not valid JSON.",
            )
        intent = payload.get("intent", "UNKNOWN")
        confidence = payload.get("confidence", 0.0)
        reason = payload.get("reason", "")
        return IntentClassification(intent=str(intent), confidence=float(confidence), reason=str(reason))
