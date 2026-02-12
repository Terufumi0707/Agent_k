from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_get_order_by_n_number_success() -> None:
    response = client.get("/v1/orders/by-n-number/N123456789")
    assert response.status_code == 200
    payload = response.json()

    assert payload["identifiers"]["n_number"] == "N123456789"
    assert payload["identifiers"]["web_entry_id"] == "UN1234567890"
    assert payload["order_status"]["status"] == "CONFIRMED"
    assert len(payload["construction"]) == 2
    assert payload["construction"][0]["scheduled"]["date"] == "2026-02-01"
    assert payload["construction"][0]["scheduled"]["time_slot"] == "09:00～12:00"
    assert payload["construction"][1]["scheduled"]["date"] == "2026-02-08"
    assert payload["construction"][1]["scheduled"]["time_slot"] == "13:00～17:00"
    assert "preferred" not in payload


def test_get_order_by_web_entry_id_success_same_content() -> None:
    response_n = client.get("/v1/orders/by-n-number/N123456789")
    response_entry = client.get("/v1/orders/UN1234567890")

    assert response_n.status_code == 200
    assert response_entry.status_code == 200
    assert response_n.json() == response_entry.json()


def test_invalid_identifier_returns_400() -> None:
    response = client.get("/v1/orders/by-n-number/N123")
    assert response.status_code == 400

    payload = response.json()
    assert payload["error"]["code"] == "INVALID_IDENTIFIER"
    assert payload["error"]["trace_id"]


def test_not_found_returns_404() -> None:
    response = client.get("/v1/orders/UN0000000000")
    assert response.status_code == 404

    payload = response.json()
    assert payload["error"]["code"] == "NOT_FOUND"


def test_multiple_matches_returns_409() -> None:
    response = client.get("/v1/orders/by-n-number/N222222222")
    assert response.status_code == 409

    payload = response.json()
    assert payload["error"]["code"] == "MULTIPLE_MATCHES"


def test_scheduled_is_always_present_and_preferred_absent() -> None:
    response = client.get("/v1/orders/UN0000000002")
    assert response.status_code == 200

    payload = response.json()
    for item in payload["construction"]:
        assert "scheduled" in item
        assert item["scheduled"]["date"]
        assert item["scheduled"]["time_slot"]
        assert "preferred" not in item
