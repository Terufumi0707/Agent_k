from __future__ import annotations

from typing import Any, Callable

from app.intent_classifier import IntentClassification, IntentClassifier
from app.llm_client import generate_with_system_and_user
from app.patch_generator import PatchGenerator
from app.services.create_entry_service import (
    AGENT_SYSTEM_PROMPT,
    FORMATTER_AGENT_SYSTEM_PROMPT,
    JUDGE_AGENT_SYSTEM_PROMPT,
    CHANGE_PREVIEW_FORMATTER_AGENT_SYSTEM_PROMPT,
    FORMATTER_PROMPT_FILE_PATH,
    JUDGE_PROMPT_FILE_PATH,
    CHANGE_PREVIEW_FORMATTER_PROMPT_FILE_PATH,
    PROMPT_FILE_PATH,
    CHANGE_PREVIEW_AGENT_SYSTEM_PROMPT,
    CHANGE_PREVIEW_PROMPT_FILE_PATH,
    CreateEntryService,
)
from app.session_store import InMemorySessionStore, SessionState, SessionStore


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
        self._service = CreateEntryService(
            session_store=session_store or InMemorySessionStore(),
            intent_classifier=intent_classifier or IntentClassifier(),
            patch_generator=patch_generator or PatchGenerator(),
            llm_client=generate_with_system_and_user,
        )

    def run(self, user_input: str, session_id: str | None = None) -> tuple[str, str]:
        # NOTE: session_id は外部から渡されない場合に新規発行し、以後の継続対話で利用する
        session_id, session_state = self._service.ensure_session(session_id)
        intent_result = self._service.classify_intent(user_input=user_input, session_state=session_state)

        intent = intent_result.intent

        # NOTE: NEW/CHANGE/CONFIRM の分岐は、抽出→評価→整形→保存の流れを前提とする
        if intent == "NEW":
            extracted_text = self._service.extract(user_input)
            extracted_json = self._service.parse_extracted_json(extracted_text)
            judge_text = self._service.judge(extracted_text)

            user_message = self._service.format_user_message(
                extracted_json=extracted_text,
                judge_json=judge_text,
            )
            if user_message is None:
                user_message = "応答の生成に失敗しました。設定を確認した上で再度お試しください。"

            self._service.save_session(
                session_id=session_id,
                extracted_json=extracted_json,
                extracted_json_raw=extracted_text,
                judge_json=judge_text,
                user_message=user_message,
                intent_result=intent_result,
            )
            return user_message, session_id

        # NOTE: CHANGE は保持済みの抽出結果に対して、変更指示のみを反映したプレビューを作成する
        if intent == "CHANGE":
            if session_state is None:
                return "変更対象となる情報がありません。", session_id

            preview_extracted_json = self._service.build_preview_extracted_json_direct(
                extracted_json=session_state.extracted_json,
                user_change_input=user_input,
            )
            user_message = self._service.format_change_preview_message(
                preview_extracted_json=preview_extracted_json,
            )
            self._service.save_change_session(
                session_id=session_id,
                session_state=session_state,
                pending_patch=None,
                preview_extracted_json=preview_extracted_json,
                user_message=user_message,
                intent_result=intent_result,
            )
            return user_message, session_id

        # NOTE: CONFIRM は確定メッセージのみを返し、外部への適用は別途実装に委ねる
        if intent == "CONFIRM":
            return "内容を確定しました。ありがとうございます。", session_id

        return "ご要望の内容をもう少し詳しく教えてください。", session_id

    def run_stream(
        self,
        user_input: str,
        session_id: str | None = None,
        on_phase: Callable[[str, str, str], None] | None = None,
    ) -> tuple[str, str]:
        def notify(phase: str, detail: str) -> None:
            if on_phase is not None:
                on_phase(phase, detail, session_id)

        session_id, session_state = self._service.ensure_session(session_id)
        notify("PHASE1_SESSION_READY", "session_id を確定しました。")

        notify("PHASE2_INTENT_CLASSIFY", "IntentClassifier を実行します。")
        intent_result = self._service.classify_intent(user_input=user_input, session_state=session_state)

        intent = intent_result.intent

        if intent == "NEW":
            notify("PHASE0_EXTRACT", "情報抽出エージェントを実行します。")
            extracted_text = self._service.extract(user_input)
            extracted_json = self._service.parse_extracted_json(extracted_text)
            notify("PHASE0_JUDGE", "Judge エージェントを実行します。")
            judge_text = self._service.judge(extracted_text)

            notify("PHASE0_FORMAT", "Formatter でユーザー表示文を生成します。")
            user_message = self._service.format_user_message(
                extracted_json=extracted_text,
                judge_json=judge_text,
            )
            if user_message is None:
                user_message = "応答の生成に失敗しました。設定を確認した上で再度お試しください。"

            notify("PHASE1_SAVE", "セッションを保存します。")
            self._service.save_session(
                session_id=session_id,
                extracted_json=extracted_json,
                extracted_json_raw=extracted_text,
                judge_json=judge_text,
                user_message=user_message,
                intent_result=intent_result,
            )
            return user_message, session_id

        if intent == "CHANGE":
            if session_state is None:
                notify("PHASE0_FORMAT", "変更対象がないためメッセージを返します。")
                return "変更対象となる情報がありません。", session_id

            notify("PHASE3_CHANGE_PREVIEW", "変更指示からプレビューJSONを生成します。")
            preview_extracted_json = self._service.build_preview_extracted_json_direct(
                extracted_json=session_state.extracted_json,
                user_change_input=user_input,
            )
            notify("PHASE0_FORMAT", "変更後内容の確認メッセージを生成します。")
            user_message = self._service.format_change_preview_message(
                preview_extracted_json=preview_extracted_json,
            )
            notify("PHASE1_SAVE", "変更内容のプレビューを保存します。")
            self._service.save_change_session(
                session_id=session_id,
                session_state=session_state,
                pending_patch=None,
                preview_extracted_json=preview_extracted_json,
                user_message=user_message,
                intent_result=intent_result,
            )
            return user_message, session_id

        if intent == "CONFIRM":
            return "内容を確定しました。ありがとうございます。", session_id

        return "ご要望の内容をもう少し詳しく教えてください。", session_id

    def _run_judge(self, extracted_text: str) -> str:
        return self._service.judge(extracted_text)

    def _build_user_message(self, extracted_json: str, judge_json: str) -> str:
        return self._service.format_user_message(extracted_json=extracted_json, judge_json=judge_json)

    def _generate_patch(self, user_change_input: str, session_state: SessionState | None) -> dict[str, Any]:
        return self._service.generate_patch(user_change_input=user_change_input, session_state=session_state)

    def _build_change_message(self, patches: dict[str, Any]) -> str:
        return self._service.build_change_message(patches)

    def classify_intent(self, user_input: str, session_id: str | None = None) -> IntentClassification:
        session_state = None
        if session_id is not None:
            session_state = self._service.get_session_state(session_id)
        return self._service.classify_intent(user_input=user_input, session_state=session_state)
