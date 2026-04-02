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
        "theme": "営業提案の標準化",
        "target_company": "株式会社サンプル",
        "background": "案件化率が低下している",
        "issues": "提案品質のばらつき",
        "goal": "受注率の改善",
        "additional_requirements": "初回はA4 5ページ想定",
    }

    response = client.post("/api/proposal/create", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "looker_data" in body["data"]
    assert "gemini_summary" in body["data"]
    assert "gas_result" in body["data"]
