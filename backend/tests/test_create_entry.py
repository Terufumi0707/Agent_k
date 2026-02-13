from fastapi.testclient import TestClient
import pytest

from app.domain.order import Order, OrderStatus
from app.main import app
import app.controllers.agent_controller as agent_controller


@pytest.fixture(autouse=True)
def reset_repository_state() -> None:
    agent_controller._order_repository.seed_defaults()


def test_create_entry_uses_orchestrator_and_returns_text(monkeypatch):
    client = TestClient(app)

    async def mock_run(prompt: str, session_id: str | None = None) -> tuple[str, str]:
        assert prompt == "そのまま渡す文字列"
        assert session_id is None
        return "ユーザー向け整形結果", "session-123"

    monkeypatch.setattr(agent_controller._orchestrator, "run", mock_run)

    response = client.post("/api/create_entry", json={"prompt": "そのまま渡す文字列"})
    assert response.status_code == 200
    assert response.json() == {"result": "ユーザー向け整形結果", "session_id": "session-123"}


def test_get_orders_filters_by_status_coordinate_only():
    client = TestClient(app)
    repository = agent_controller._order_repository
    repository.clear()

    delivery_order = Order.create(session_id="session-delivery", current_status=OrderStatus.DELIVERY)
    coordinate_order = Order.create(session_id="session-coordinate", current_status=OrderStatus.COORDINATE)
    repository.save(delivery_order)
    repository.save(coordinate_order)

    response = client.get("/api/orders", params={"status": "COORDINATE"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == coordinate_order.id
    assert body[0]["session_id"] == "session-coordinate"
    assert body[0]["current_status"] == "COORDINATE"


def test_get_orders_without_status_returns_all_orders():
    client = TestClient(app)
    repository = agent_controller._order_repository
    repository.clear()

    delivery_order = Order.create(session_id="session-delivery", current_status=OrderStatus.DELIVERY)
    backyard_order = Order.create(session_id="session-backyard", current_status=OrderStatus.BACKYARD)
    repository.save(delivery_order)
    repository.save(backyard_order)

    response = client.get("/api/orders")

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [delivery_order.id, backyard_order.id]
    assert [item["current_status"] for item in body] == ["DELIVERY", "BACKYARD"]


def test_get_orders_returns_seeded_orders_on_startup():
    client = TestClient(app)

    response = client.get("/api/orders")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 9
    assert body[0]["id"] == "order-delivery-001"
    assert body[0]["session_id"] == "session-delivery-001"
    assert body[0]["current_status"] == "DELIVERY"
    assert "通信事業者" in body[0]["summary"]
