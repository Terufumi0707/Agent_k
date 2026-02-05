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
