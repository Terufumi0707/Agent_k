import json

import app.intent_classifier as intent_classifier
from app.intent_classifier import IntentClassifier
from app.session_store import SessionState


def test_intent_classifier_calls_llm_with_session_summary(monkeypatch):
    captured = {}

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return json.dumps(
            {"intent": "CHANGE", "confidence": 0.7, "reason": "追加入力で修正依頼"},
            ensure_ascii=False,
        )

    monkeypatch.setattr(intent_classifier, "generate_with_system_and_user", mock_generate_with_system_and_user)

    state = SessionState(
        extracted_json="{\"field\": \"value\"}",
        judge_result="{\"judge\": true}",
        user_view_message="確認メッセージ",
        intent_result="{\"intent\": \"NEW\"}",
        pending_patch=None,
        preview_extracted_json=None,
    )
    result = IntentClassifier().classify("日程を変更したい", state)

    assert captured["system_prompt"] == intent_classifier.INTENT_AGENT_SYSTEM_PROMPT
    assert "latest_input:\n日程を変更したい" in captured["user_prompt"]
    assert "session_summary:" in captured["user_prompt"]
    assert "\"extracted_json\"" in captured["user_prompt"]
    assert result.intent == "CHANGE"
    assert result.confidence == 0.7
    assert result.reason == "追加入力で修正依頼"


def test_intent_classifier_handles_invalid_json():
    result = IntentClassifier()._parse_response("not-json")
    assert result.intent == "UNKNOWN"
    assert result.confidence == 0.0
    assert result.reason
