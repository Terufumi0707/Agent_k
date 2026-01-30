import os

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.session import session_store


@pytest.fixture(autouse=True)
def clear_sessions():
    session_store.clear()
    yield
    session_store.clear()


def test_start_missing_identifier():
    client = TestClient(app)
    payload = {
        "work_changes": [
            {"work_type": "メイン回線_開通", "desired_date": "2026-02-10"}
        ]
    }
    response = client.post("/intake/start", json=payload)
    data = response.json()
    assert data["status"] == "need_more_info"
    assert "identifier" in data["missing_fields"]


def test_start_missing_work_changes():
    client = TestClient(app)
    payload = {"a_number": "A-100"}
    response = client.post("/intake/start", json=payload)
    data = response.json()
    assert data["status"] == "need_more_info"
    assert "work_changes" in data["missing_fields"]


def test_next_partial_completion():
    client = TestClient(app)
    start_payload = {"a_number": "A-100"}
    start_response = client.post("/intake/start", json=start_payload)
    session_id = start_response.json()["session_id"]

    next_payload = {
        "session_id": session_id,
        "work_changes": [{"work_type": "メイン回線_開通", "desired_date": None}],
    }
    next_response = client.post("/intake/next", json=next_payload)
    data = next_response.json()
    assert data["status"] == "need_more_info"
    assert "work_changes[0].desired_date" in data["missing_fields"]


def test_completed_message():
    client = TestClient(app)
    payload = {
        "entry_id": "ENT-001",
        "work_changes": [
            {"work_type": "メイン回線_開通", "desired_date": "2026-02-10"}
        ],
    }
    response = client.post("/intake/start", json=payload)
    data = response.json()
    assert data["status"] == "completed"
    assert data["message"] == "受付完了しました"


def test_invalid_session_id():
    client = TestClient(app)
    payload = {"session_id": "missing", "a_number": "A-100"}
    response = client.post("/intake/next", json=payload)
    data = response.json()
    assert data["status"] == "invalid_request"


def test_fetch_current_order(monkeypatch):
    client = TestClient(app)
    base_url = "http://test-api"
    os.environ["SYSTEM_API_BASE_URL"] = base_url

    def mock_get(url, timeout):
        assert url == f"{base_url}/orders/by-a-number/A-100"
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={
                "main_a_number": "A-12345",
                "backup_a_number": "A-67890",
                "main_work_types": ["メイン回線_開通"],
                "main_work_date": ["2026-02-01"],
                "backup_work_types": ["バックアップ回線_撤去"],
                "backup_work_date": ["2026-02-05"],
            },
            request=request,
        )

    monkeypatch.setattr(httpx, "get", mock_get)

    payload = {
        "a_number": "A-100",
        "fetch_current_order": True,
        "work_changes": [
            {"work_type": "メイン回線_開通", "desired_date": "2026-02-10"}
        ],
    }
    response = client.post("/intake/start", json=payload)
    data = response.json()
    assert data["status"] == "completed"
    assert data["order_info"]["main_a_number"] == "A-12345"


def test_message_parsing():
    client = TestClient(app)
    payload = {
        "message": "A-99999 工事種別: メイン回線_開通 希望日: 2026-02-10",
        "fetch_current_order": False,
    }
    response = client.post("/intake/start", json=payload)
    data = response.json()
    assert data["status"] == "completed"
    assert data["missing_fields"] == []
