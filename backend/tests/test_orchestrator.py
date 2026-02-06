import json

import app.orchestrator as orchestrator


def test_orchestrator_calls_agent_once_with_system_prompt(monkeypatch):
    captured = {"count": 0, "system_prompt": "", "user_prompt": ""}

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured["count"] += 1
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "agent-result"

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    result = orchestrator.CreateEntryOrchestrator().run("PlaceHolderのRequest")

    assert captured["count"] == 1
    assert captured["system_prompt"] == orchestrator.AGENT_SYSTEM_PROMPT
    assert captured["user_prompt"] == "PlaceHolderのRequest"
    assert result == "agent-result"


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
