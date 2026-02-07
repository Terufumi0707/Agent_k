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
    """create_entry の処理順序を統一するオーケストレーター。"""

    def __init__(
        self,
        session_store: SessionStore | None = None,
        intent_classifier: IntentClassifier | None = None,
        patch_generator: PatchGenerator | None = None,
    ) -> None:
        self._session_store = session_store or InMemorySessionStore()
        self._intent_classifier = intent_classifier or IntentClassifier()
        self._patch_generator = patch_generator or PatchGenerator()

    def run(self, prompt: str, session_id: str | None = None) -> tuple[str, str]:
        if session_id is None:
            session_id = generate_session_id()
        # 1. 最新入力とセッション状態をもとに意図判定（処理分岐の判断材料）
        intent_result = self.classify_intent(prompt, session_id)
        # 2. 入力から必要情報を抽出
        extracted_result = generate_with_system_and_user(
            system_prompt=AGENT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        # 3. 抽出結果を評価
        judge_result = self.run_judge(extracted_result)
        extracted_payload = self._to_json_text(extracted_result)
        judge_payload = self._to_json_text(judge_result)
        # 4. 抽出結果・評価結果をもとにユーザー向け文面を生成
        user_message = self.build_user_message(extracted_payload, judge_payload)
        # 5. セッション状態として保存（意図判定結果も含める）
        # Phase1: 変更対応は行わず、処理結果をセッション単位で保存するだけに留める。
        self._session_store.save(
            session_id,
            SessionState(
                extracted_json=extracted_payload,
                judge_result=judge_payload,
                user_view_message=user_message,
                intent_result=self._to_json_text(intent_result.__dict__),
            ),
        )
        return user_message, session_id

    def run_judge(self, prompt: str) -> str:
        """情報抽出JSONの評価を行うJudgeエージェントを実行する。"""

        return generate_with_system_and_user(
            system_prompt=JUDGE_AGENT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

    def build_user_message(self, extracted_result: dict[str, Any] | str, judge_result: dict[str, Any] | str) -> str:
        """抽出結果JSONとJudge結果JSONを入力として、ユーザー表示文を生成する。"""

        extracted_payload = self._to_json_text(extracted_result)
        judge_payload = self._to_json_text(judge_result)
        user_prompt = f"extracted_result:\n{extracted_payload}\n\njudge_result:\n{judge_payload}"

        return generate_with_system_and_user(
            system_prompt=FORMATTER_AGENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    def _to_json_text(self, payload: dict[str, Any] | str) -> str:
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False)

    def classify_intent(self, prompt: str, session_id: str | None = None) -> IntentClassification:
        session_state = None
        if session_id is not None:
            session_state = self._session_store.get(session_id)
        return self._intent_classifier.classify(prompt, session_state)

    def generate_patch(self, user_change_input: str, session_id: str | None = None) -> dict[str, Any]:
        if session_id is None:
            return {"patches": []}
        session_state = self._session_store.get(session_id)
        if session_state is None:
            return {"patches": []}
        return self._patch_generator.generate(
            user_change_input=user_change_input,
            extracted_json=session_state.extracted_json,
        )
