import json

import app.orchestrator as orchestrator
from app.intent_classifier import IntentClassification
from app.session_store import InMemorySessionStore, SessionState


def test_orchestrator_run_executes_full_pipeline_and_returns_formatter_result(monkeypatch):
    captured: list[tuple[str, str]] = []

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured.append((system_prompt, user_prompt))
        if system_prompt == orchestrator.AGENT_SYSTEM_PROMPT:
            return '{"extracted": true}'
        if system_prompt == orchestrator.JUDGE_AGENT_SYSTEM_PROMPT:
            assert user_prompt == '{"extracted": true}'
            return '{"judge": "ok"}'
        if system_prompt == orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT:
            assert 'extracted_result:\n{"extracted": true}' in user_prompt
            assert 'judge_result:\n{"judge": "ok"}' in user_prompt
            return "display-message"
        raise AssertionError("unexpected system prompt")

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    class DummyIntentClassifier:
        def __init__(self) -> None:
            self.count = 0

        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            self.count += 1
            assert user_input == "PlaceHolderのRequest"
            assert session_state is None
            return IntentClassification(intent="NEW", confidence=0.8, reason="新規入力")

    dummy_classifier = DummyIntentClassifier()
    store = InMemorySessionStore()
    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=store,
        intent_classifier=dummy_classifier,
    ).run("PlaceHolderのRequest")

    assert dummy_classifier.count == 1
    assert len(captured) == 3
    assert captured[0] == (orchestrator.AGENT_SYSTEM_PROMPT, "PlaceHolderのRequest")
    assert captured[1] == (orchestrator.JUDGE_AGENT_SYSTEM_PROMPT, '{"extracted": true}')
    assert captured[2][0] == orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT
    assert result == "display-message"
    assert isinstance(session_id, str)
    state = store.get(session_id)
    assert state is not None
    assert state.extracted_json == '{"extracted": true}'
    assert state.extracted_json_raw == '{"extracted": true}'


def test_orchestrator_system_prompt_loaded_from_file():
    file_prompt = orchestrator.PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
    assert orchestrator.AGENT_SYSTEM_PROMPT == file_prompt


def test_orchestrator_run_judge_calls_agent_once_with_judge_system_prompt(monkeypatch):
    captured = {"count": 0, "system_prompt": "", "user_prompt": ""}

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured["count"] += 1
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "judge-agent-result"

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    result = orchestrator.CreateEntryOrchestrator()._run_judge("抽出JSON")

    assert captured["count"] == 1
    assert captured["system_prompt"] == orchestrator.JUDGE_AGENT_SYSTEM_PROMPT
    assert captured["user_prompt"] == "抽出JSON"
    assert result == "judge-agent-result"


def test_judge_system_prompt_loaded_from_file():
    file_prompt = orchestrator.JUDGE_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
    assert orchestrator.JUDGE_AGENT_SYSTEM_PROMPT == file_prompt


def test_orchestrator_build_user_message_calls_formatter_agent(monkeypatch):
    captured = {"count": 0, "system_prompt": "", "user_prompt": ""}

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured["count"] += 1
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "display-message"

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    extracted_result = {"construction_types": [{"normalized_type": "切替工事"}]}
    judge_result = {"judge_result": {"status": "CONFIRM"}}

    result = orchestrator.CreateEntryOrchestrator()._build_user_message(
        extracted_json=json.dumps(extracted_result, ensure_ascii=False),
        judge_json=json.dumps(judge_result, ensure_ascii=False),
    )

    assert captured["count"] == 1
    assert captured["system_prompt"] == orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT
    assert "extracted_result:\n" in captured["user_prompt"]
    assert "judge_result:\n" in captured["user_prompt"]
    assert json.dumps(extracted_result, ensure_ascii=False) in captured["user_prompt"]
    assert json.dumps(judge_result, ensure_ascii=False) in captured["user_prompt"]
    assert result == "display-message"


def test_formatter_system_prompt_loaded_from_file():
    file_prompt = orchestrator.FORMATTER_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
    assert orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT == file_prompt


def test_generate_patch_returns_parsed_patches(monkeypatch):
    store = InMemorySessionStore()
    store.save(
        "session-123",
        SessionState(
            extracted_json='{"preferred_dates": [{"priority": 1, "date": "2026-04-01"}]}',
            judge_result="{}",
            user_view_message="",
            intent_result="{}",
            pending_patch=None,
            preview_extracted_json=None,
        ),
    )

    def mock_generate(user_change_input: str, extracted_json: str) -> dict[str, object]:
        assert user_change_input == "希望日を変えてください"
        assert extracted_json == '{"preferred_dates": [{"priority": 1, "date": "2026-04-01"}]}'
        return {
            "patches": [
                {
                    "operation": "update",
                    "target": "preferred_dates[priority=1].date",
                    "value": "2026-04-02",
                    "reason": "ユーザーが希望日を変更すると明示したため",
                }
            ]
        }

    patch_generator = orchestrator.PatchGenerator(system_prompt="prompt")
    monkeypatch.setattr(patch_generator, "generate", mock_generate)

    result = orchestrator.CreateEntryOrchestrator(
        session_store=store,
        patch_generator=patch_generator,
    )._generate_patch("希望日を変えてください", session_state=store.get("session-123"))

    assert result == {
        "patches": [
            {
                "operation": "update",
                "target": "preferred_dates[priority=1].date",
                "value": "2026-04-02",
                "reason": "ユーザーが希望日を変更すると明示したため",
            }
        ]
    }


def test_orchestrator_change_intent_returns_change_preview_message(monkeypatch):
    store = InMemorySessionStore()
    store.save(
        "session-456",
        SessionState(
            extracted_json='{"preferred_dates": [{"priority": 1, "date": "2026-04-01"}]}',
            judge_result="{}",
            user_view_message="",
            intent_result="{}",
            pending_patch=None,
            preview_extracted_json=None,
        ),
    )

    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            assert user_input == "希望日を変えてください"
            assert session_state is not None
            return IntentClassification(intent="CHANGE", confidence=0.9, reason="変更依頼")

    captured: list[tuple[str, str]] = []

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured.append((system_prompt, user_prompt))
        if system_prompt == orchestrator.CHANGE_PREVIEW_AGENT_SYSTEM_PROMPT:
            assert "extracted_json:\n" in user_prompt
            assert "user_change_input:\n希望日を変えてください" in user_prompt
            return '{"preferred_dates": [{"priority": 1, "date": "2026-04-02"}]}'
        if system_prompt == orchestrator.CHANGE_PREVIEW_FORMATTER_AGENT_SYSTEM_PROMPT:
            assert "preview_extracted_json:\n" in user_prompt
            return "変更後の内容の要約"
        raise AssertionError("unexpected system prompt")

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=store,
        intent_classifier=DummyIntentClassifier(),
    ).run("希望日を変えてください", session_id="session-456")

    assert result == (
        "変更後の内容の要約\n\nこの内容でよろしければ確定してください。\nさらに変更があれば指示してください。"
    )
    assert session_id == "session-456"
    assert len(captured) == 2


def test_orchestrator_change_intent_without_session_returns_missing_target_message():
    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            assert user_input == "変更してください"
            assert session_state is None
            return IntentClassification(intent="CHANGE", confidence=0.9, reason="変更依頼")

    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=InMemorySessionStore(),
        intent_classifier=DummyIntentClassifier(),
    ).run("変更してください")

    assert result == "変更対象となる情報がありません。"
    assert isinstance(session_id, str)
