import json

import app.orchestrator as orchestrator


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

    intent_calls = {"count": 0}

    def mock_classify_intent(
        self, prompt: str, session_id: str | None = None
    ) -> orchestrator.IntentClassification:
        intent_calls["count"] += 1
        return orchestrator.IntentClassification(intent="NEW", confidence=0.8, reason="新規入力")

    monkeypatch.setattr(orchestrator.CreateEntryOrchestrator, "classify_intent", mock_classify_intent)

    result = orchestrator.CreateEntryOrchestrator().run("PlaceHolderのRequest")

    assert intent_calls["count"] == 1
    assert len(captured) == 3
    assert captured[0] == (orchestrator.AGENT_SYSTEM_PROMPT, "PlaceHolderのRequest")
    assert captured[1] == (orchestrator.JUDGE_AGENT_SYSTEM_PROMPT, '{"extracted": true}')
    assert captured[2][0] == orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT
    assert result == "display-message"


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

    result = orchestrator.CreateEntryOrchestrator().run_judge("抽出JSON")

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

    result = orchestrator.CreateEntryOrchestrator().build_user_message(extracted_result, judge_result)

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
