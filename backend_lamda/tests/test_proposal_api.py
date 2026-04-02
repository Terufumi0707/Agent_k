from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_proposal():
    client = TestClient(app)
    payload = {
        "theme": "新規顧客向けオンボーディング改善",
        "objective": "初回契約から稼働までの期間短縮",
        "constraints": ["予算据え置き", "3か月以内に実施"],
        "audience": "営業本部",
    }

    response = client.post("/api/proposals", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "提案書（ドラフト）" in body["title"]
    assert len(body["sections"]) == 5
