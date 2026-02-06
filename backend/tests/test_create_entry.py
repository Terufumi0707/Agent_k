from fastapi.testclient import TestClient

from app.main import app
import app.controllers.agent_controller as agent_controller


def test_create_entry_uses_orchestrator_and_returns_text(monkeypatch):
    client = TestClient(app)

    def mock_run(prompt: str, session_id: str | None = None) -> tuple[str, str]:
        assert prompt == "そのまま渡す文字列"
        assert session_id is None
        return "ユーザー向け整形結果", "session-123"

    monkeypatch.setattr(agent_controller._orchestrator, "run", mock_run)

    response = client.post("/api/create_entry", json={"prompt": "そのまま渡す文字列"})
    assert response.status_code == 200
    assert response.json() == {"result": "ユーザー向け整形結果", "session_id": "session-123"}
