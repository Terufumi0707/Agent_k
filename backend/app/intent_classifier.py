from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    """
    ユーザー入力の意図を NEW / CHANGE / CONFIRM / UNKNOWN に分類する。

    NOTE:
    - LLMの出力は揺れ（大小文字、空白、想定外値、型揺れ）が起こり得るため、ここで正規化・安全化する。
    - 初回（session_state is None）は参照元が無いので CHANGE を許可しない（原則 NEW、例外は明確な CONFIRM のみ）。
    """

    _ALLOWED_INTENTS = {"NEW", "CHANGE", "CONFIRM", "UNKNOWN"}

    def __init__(self) -> None:
        self._system_prompt = INTENT_AGENT_SYSTEM_PROMPT

    def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
        summary = self._build_session_summary(session_state)
        user_prompt = f"latest_input:\n{user_input}\n\nsession_summary:\n{summary}"
        raw_response = generate_with_system_and_user(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
        )
        result = self._parse_response(raw_response)

        # 初回（状態なし）では CHANGE を成立させない：原則 NEW、短文の確定のみ CONFIRM
        if session_state is None:
            return self._override_intent_for_empty_session(user_input, result)

        return result

    def _build_session_summary(self, session_state: SessionState | None) -> str:
        if session_state is None:
            return "null"
        payload: dict[str, Any] = {
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
        intent_raw = payload.get("intent", "UNKNOWN")
        intent = self._normalize_intent(intent_raw)

        confidence_raw = payload.get("confidence", 0.0)
        confidence = self._safe_float(confidence_raw, default=0.0)

        reason_raw = payload.get("reason", "")
        reason = str(reason_raw) if reason_raw is not None else ""

        return IntentClassification(intent=intent, confidence=confidence, reason=reason)

    def _normalize_intent(self, intent_value: Any) -> str:
        text = str(intent_value).strip().upper()
        if text not in self._ALLOWED_INTENTS:
            return "UNKNOWN"
        return text

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _override_intent_for_empty_session(
        self,
        user_input: str,
        result: IntentClassification,
    ) -> IntentClassification:
        """
        初回（session_state is None）では参照すべき過去状態が無い。
        - 明確な確定（短文）なら CONFIRM を許可
        - それ以外は NEW に寄せる（LLMがCHANGE/UNKNOWNでもNEWに補正）
        """
        if self._is_confirm_message(user_input):
            if result.intent == "CONFIRM":
                return result
            return IntentClassification(
                intent="CONFIRM",
                confidence=max(result.confidence, 0.5),
                reason="Session is empty; input matched confirmation message.",
            )

        if result.intent == "NEW":
            return result

        # 初回は CHANGE を許可しないため NEW に補正する
        return IntentClassification(
            intent="NEW",
            confidence=max(result.confidence, 0.5),
            reason="Session is empty; defaulting to NEW per rules.",
        )

    def _is_confirm_message(self, user_input: str) -> bool:
        """
        短文の承認/確定だけを CONFIRM とみなす（長文メール本文の誤判定を避ける）。
        - 文字数が短い場合のみ判定対象（目安: 30文字以下）
        - キーワード含有で判定（全文一致に依存しない）
        """
        text = user_input.strip()
        if not text:
            return False

        # 長文はCONFIRMにしない（メール本文などの誤判定防止）
        if len(text) > 30:
            return False

        normalized = text.lower()

        # 英語系
        if re.fullmatch(r"(ok|okay|confirm)", normalized):
            return True

        # 日本語系（部分一致も許容）
        confirm_keywords = [
            "ok",
            "了解",
            "承知",
            "確認しました",
            "問題ありません",
            "その内容でお願いします",
            "それでお願いします",
            "確定",
            "同意",
            "お願いします",
        ]
        return any(k in text for k in confirm_keywords)
