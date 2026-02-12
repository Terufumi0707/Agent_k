from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from app.intent_classifier import IntentClassification, IntentClassifier
from app.llm_client import generate_with_system_and_user
from app.patch_generator import PatchGenerator
from app.session_store import InMemorySessionStore, SessionState, SessionStore, generate_session_id

PROMPT_FILE_PATH = Path(__file__).parent.parent / "prompts" / "create_entry_agent_system_prompt.txt"
AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
JUDGE_PROMPT_FILE_PATH = Path(__file__).parent.parent / "prompts" / "judge_extraction_agent_system_prompt.txt"
JUDGE_AGENT_SYSTEM_PROMPT = JUDGE_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
FORMATTER_PROMPT_FILE_PATH = Path(__file__).parent.parent / "prompts" / "user_message_formatter_agent_system_prompt.txt"
FORMATTER_AGENT_SYSTEM_PROMPT = FORMATTER_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
PATCH_PREVIEW_PROMPT_FILE_PATH = (
    Path(__file__).parent.parent / "prompts" / "patch_preview_agent_system_prompt.txt"
)
PATCH_PREVIEW_AGENT_SYSTEM_PROMPT = PATCH_PREVIEW_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
CHANGE_PREVIEW_PROMPT_FILE_PATH = (
    Path(__file__).parent.parent / "prompts" / "change_preview_agent_system_prompt.txt"
)
CHANGE_PREVIEW_AGENT_SYSTEM_PROMPT = CHANGE_PREVIEW_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
CHANGE_PREVIEW_FORMATTER_PROMPT_FILE_PATH = (
    Path(__file__).parent.parent / "prompts" / "change_preview_formatter_agent_system_prompt.txt"
)
CHANGE_PREVIEW_FORMATTER_AGENT_SYSTEM_PROMPT = CHANGE_PREVIEW_FORMATTER_PROMPT_FILE_PATH.read_text(
    encoding="utf-8"
).strip()
QUERY_STATUS_ROUTER_PROMPT_FILE_PATH = (
    Path(__file__).parent.parent / "prompts" / "query_status_router_agent_system_prompt.txt"
)
QUERY_STATUS_ROUTER_AGENT_SYSTEM_PROMPT = QUERY_STATUS_ROUTER_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


class CreateEntryService:
    def __init__(
        self,
        session_store: SessionStore | None = None,
        intent_classifier: IntentClassifier | None = None,
        patch_generator: PatchGenerator | None = None,
        llm_client: Callable[[str, str], str] = generate_with_system_and_user,
    ) -> None:
        self._session_store = session_store or InMemorySessionStore()
        self._intent_classifier = intent_classifier or IntentClassifier()
        self._patch_generator = patch_generator or PatchGenerator()
        self._llm_client = llm_client

    def ensure_session(self, session_id: str | None) -> tuple[str, SessionState | None]:
        if session_id is None:
            session_id = generate_session_id()
        return session_id, self._session_store.get(session_id)

    def classify_intent(self, user_input: str, session_state: SessionState | None) -> IntentClassification:
        return self._intent_classifier.classify(user_input=user_input, session_state=session_state)

    def extract(self, user_input: str) -> str:
        return self._llm_client(
            system_prompt=AGENT_SYSTEM_PROMPT,
            user_prompt=user_input,
        )

    def judge(self, extracted_text: str) -> str:
        return self._llm_client(
            system_prompt=JUDGE_AGENT_SYSTEM_PROMPT,
            user_prompt=extracted_text,
        )

    def parse_extracted_json(self, extracted_text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(extracted_text)
        except json.JSONDecodeError:
            return {"raw_text": extracted_text}

        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}

    def format_user_message(self, extracted_json: str, judge_json: str) -> str:
        user_prompt = f"extracted_result:\n{extracted_json}\n\njudge_result:\n{judge_json}"
        return self._llm_client(
            system_prompt=FORMATTER_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    def save_session(
        self,
        session_id: str,
        extracted_json: dict[str, Any],
        extracted_json_raw: str,
        judge_json: str,
        user_message: str,
        intent_result: IntentClassification,
    ) -> None:
        self._session_store.save(
            session_id,
            SessionState(
                extracted_json=self.to_json_text(extracted_json),
                extracted_json_raw=extracted_json_raw,
                judge_result=judge_json,
                user_view_message=user_message,
                intent_result=self.to_json_text(intent_result.__dict__),
                pending_patch=None,
                preview_extracted_json=None,
                last_lookup=None,
            ),
        )

    def save_change_session(
        self,
        session_id: str,
        session_state: SessionState,
        pending_patch: dict[str, Any] | None,
        preview_extracted_json: str,
        user_message: str,
        intent_result: IntentClassification,
    ) -> None:
        self._session_store.save(
            session_id,
            SessionState(
                extracted_json=session_state.extracted_json,
                extracted_json_raw=session_state.extracted_json_raw,
                judge_result=session_state.judge_result,
                user_view_message=user_message,
                intent_result=self.to_json_text(intent_result.__dict__),
                pending_patch=self.to_json_text(pending_patch) if pending_patch is not None else None,
                preview_extracted_json=preview_extracted_json,
                last_lookup=session_state.last_lookup,
            ),
        )

    def save_lookup_session(
        self,
        session_id: str,
        session_state: SessionState | None,
        user_message: str,
        lookup_state: dict[str, Any],
    ) -> None:
        self._session_store.save(
            session_id,
            SessionState(
                extracted_json=session_state.extracted_json if session_state is not None else "{}",
                extracted_json_raw=session_state.extracted_json_raw if session_state is not None else None,
                judge_result=session_state.judge_result if session_state is not None else "{}",
                user_view_message=user_message,
                intent_result=self.to_json_text({"intent": "QUERY_STATUS"}),
                pending_patch=session_state.pending_patch if session_state is not None else None,
                preview_extracted_json=session_state.preview_extracted_json if session_state is not None else None,
                last_lookup=self.to_json_text(lookup_state),
            ),
        )


    def route_query_status(self, user_input: str) -> dict[str, Any]:
        router_text = self._llm_client(
            system_prompt=QUERY_STATUS_ROUTER_AGENT_SYSTEM_PROMPT,
            user_prompt=f"latest_input:\n{user_input}",
        )
        try:
            payload = json.loads(router_text)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass
        return {"n_number": None, "web_entry_id": None, "action": "NEED_IDENTIFIER", "reason": "parse_error"}

    def generate_patch(self, user_change_input: str, session_state: SessionState | None) -> dict[str, Any]:
        if session_state is None:
            return {"patches": []}
        return self._patch_generator.generate(
            user_change_input=user_change_input,
            extracted_json=session_state.extracted_json,
        )

    def build_preview_extracted_json(self, extracted_json: str, patches: dict[str, Any]) -> str:
        if not patches.get("patches"):
            return extracted_json
        user_prompt = f"extracted_json:\n{extracted_json}\n\npatches:\n{self.to_json_text(patches)}"
        return self._llm_client(
            system_prompt=PATCH_PREVIEW_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    def build_preview_extracted_json_direct(self, extracted_json: str, user_change_input: str) -> str:
        user_prompt = f"extracted_json:\n{extracted_json}\n\nuser_change_input:\n{user_change_input}"
        return self._llm_client(
            system_prompt=CHANGE_PREVIEW_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    def format_change_preview_message(self, preview_extracted_json: str) -> str:
        user_prompt = f"preview_extracted_json:\n{preview_extracted_json}"
        summary = self._llm_client(
            system_prompt=CHANGE_PREVIEW_FORMATTER_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        if not summary:
            summary = "変更後の内容を要約できませんでした。"
        return (
            f"{summary}\n\n"
            "この内容でよろしければ確定してください。\n"
            "さらに変更があれば指示してください。"
        )

    def build_change_message(self, patches: dict[str, Any]) -> str:
        if not patches.get("patches"):
            return "変更内容を特定できませんでした。もう少し具体的に教えてください。"
        return "以下の変更内容を受け付けました。問題なければ確定してください。"

    def to_json_text(self, payload: dict[str, Any] | str) -> str:
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False)

    def get_session_state(self, session_id: str) -> SessionState | None:
        return self._session_store.get(session_id)
