from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.intent_classifier import IntentClassification, IntentClassifier
from app.llm_client import generate_with_system_and_user
from app.patch_generator import PatchGenerator
from app.session_store import InMemorySessionStore, SessionState, SessionStore, generate_session_id

PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "create_entry_agent_system_prompt.txt"
AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
JUDGE_PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "judge_extraction_agent_system_prompt.txt"
JUDGE_AGENT_SYSTEM_PROMPT = JUDGE_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
FORMATTER_PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "user_message_formatter_agent_system_prompt.txt"
FORMATTER_AGENT_SYSTEM_PROMPT = FORMATTER_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


class CreateEntryOrchestrator:
    """
    Phase構成に基づいて create_entry の処理順序を制御するオーケストレーター。

    Phase0: 情報抽出
    Phase1: 状態保持
    Phase2: 意図判定
    Phase3: Patch生成
    """

    def __init__(
        self,
        session_store: SessionStore | None = None,
        intent_classifier: IntentClassifier | None = None,
        patch_generator: PatchGenerator | None = None,
    ) -> None:
        self._session_store = session_store or InMemorySessionStore()
        self._intent_classifier = intent_classifier or IntentClassifier()
        self._patch_generator = patch_generator or PatchGenerator()

    def run(self, user_input: str, session_id: str | None = None) -> tuple[str, str]:
        # NOTE: session_id は外部から渡されない場合に新規発行し、以後の継続対話で利用する
        if session_id is None:
            session_id = generate_session_id()
        session_state = self._session_store.get(session_id)

        intent_result = self._intent_classifier.classify(
            user_input=user_input,
            session_state=session_state,
        )

        intent = intent_result.intent

        # NOTE: NEW/CHANGE/CONFIRM の分岐は、抽出→評価→整形→保存の流れを前提とする
        if intent == "NEW":
            extracted_text = generate_with_system_and_user(
                system_prompt=AGENT_SYSTEM_PROMPT,
                user_prompt=user_input,
            )
            judge_text = self._run_judge(extracted_text)

            extracted_json = self._to_json_text(extracted_text)
            judge_json = self._to_json_text(judge_text)

            user_message = self._build_user_message(
                extracted_json=extracted_json,
                judge_json=judge_json,
            )

            self._session_store.save(
                session_id,
                SessionState(
                    extracted_json=extracted_json,
                    judge_result=judge_json,
                    user_view_message=user_message,
                    intent_result=self._to_json_text(intent_result.__dict__),
                ),
            )
            return user_message, session_id

        # NOTE: CHANGE は直前の抽出結果に対する差分のみ作成し、再抽出は行わない
        if intent == "CHANGE":
            patches = self._generate_patch(
                user_change_input=user_input,
                session_state=session_state,
            )
            user_message = self._build_change_message(patches)
            return user_message, session_id

        # NOTE: CONFIRM は確定メッセージのみを返し、外部への適用は別途実装に委ねる
        if intent == "CONFIRM":
            return "内容を確定しました。ありがとうございます。", session_id

        return "ご要望の内容をもう少し詳しく教えてください。", session_id

    def _run_judge(self, extracted_text: str) -> str:
        return generate_with_system_and_user(
            system_prompt=JUDGE_AGENT_SYSTEM_PROMPT,
            user_prompt=extracted_text,
        )

    def _build_user_message(self, extracted_json: str, judge_json: str) -> str:
        user_prompt = f"extracted_result:\n{extracted_json}\n\njudge_result:\n{judge_json}"
        return generate_with_system_and_user(
            system_prompt=FORMATTER_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    def _generate_patch(self, user_change_input: str, session_state: SessionState | None) -> dict[str, Any]:
        if session_state is None:
            return {"patches": []}
        return self._patch_generator.generate(
            user_change_input=user_change_input,
            extracted_json=session_state.extracted_json,
        )

    def _build_change_message(self, patches: dict[str, Any]) -> str:
        if not patches.get("patches"):
            return "変更内容を特定できませんでした。もう少し具体的に教えてください。"
        return "以下の変更内容を受け付けました。問題なければ確定してください。"

    def _to_json_text(self, payload: dict[str, Any] | str) -> str:
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False)

    def classify_intent(self, user_input: str, session_id: str | None = None) -> IntentClassification:
        session_state = None
        if session_id is not None:
            session_state = self._session_store.get(session_id)
        return self._intent_classifier.classify(user_input=user_input, session_state=session_state)
