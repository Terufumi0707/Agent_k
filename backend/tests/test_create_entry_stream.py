import json

from fastapi.testclient import TestClient

from app.main import app
import app.controllers.agent_controller as agent_controller


def _parse_event(event_block: str) -> tuple[str, dict[str, str]]:
    lines = event_block.splitlines()
    event_name = lines[0].split(":", 1)[1].strip()
    data_line = next(line for line in lines if line.startswith("data: "))
    payload = json.loads(data_line.replace("data: ", "", 1))
    return event_name, payload


def test_create_entry_stream_emits_phase_and_done(monkeypatch):
    client = TestClient(app)

    async def mock_run_stream(prompt: str, session_id: str | None = None, on_phase=None) -> tuple[str, str]:
        assert prompt == "そのまま渡す文字列"
        if session_id is None:
            session_id = "session-123"
        if on_phase:
            on_phase("PHASE1_SESSION_READY", "session ready", session_id)
            on_phase("PHASE2_INTENT_CLASSIFY", "intent classify", session_id)
        return "ユーザー向け整形結果", session_id

    monkeypatch.setattr(agent_controller._stream_service._orchestrator, "run_stream", mock_run_stream)

    with client.stream("POST", "/api/create_entry/stream", json={"prompt": "そのまま渡す文字列"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    events = [chunk for chunk in body.strip().split("\n\n") if chunk]
    assert events

    event_name, payload = _parse_event(events[0])
    assert event_name == "phase"
    assert payload["phase"] == "PHASE1_SESSION_READY"
    assert payload["session_id"] == "session-123"

    event_name, payload = _parse_event(events[-1])
    assert event_name == "done"
    assert payload["session_id"] == "session-123"
    assert payload["message"] == "ユーザー向け整形結果"
