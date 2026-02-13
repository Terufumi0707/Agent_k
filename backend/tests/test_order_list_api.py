from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient

from app.domain.order import Order, OrderStatus
from app.main import app
import app.controllers.agent_controller as agent_controller


def _make_order(order_id: str, session_id: str, status: OrderStatus, minutes: int) -> Order:
    base = datetime.now(timezone.utc)
    return Order(
        id=order_id,
        session_id=session_id,
        current_status=status,
        created_at=base - timedelta(minutes=minutes + 1),
        updated_at=base - timedelta(minutes=minutes),
    )


def test_v1_orders_returns_updated_at_desc() -> None:
    client = TestClient(app)
    repository = agent_controller._order_repository
    repository.clear()

    order_old = _make_order("o1", "s1", OrderStatus.DELIVERY, 10)
    order_new = _make_order("o2", "s2", OrderStatus.COORDINATE, 1)
    order_mid = _make_order("o3", "s3", OrderStatus.BACKYARD, 5)
    repository.save(order_old)
    repository.save(order_new)
    repository.save(order_mid)

    response = client.get("/api/v1/orders")

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert ids == ["o2", "o3", "o1"]


def test_v1_status_groups_returns_three_groups_and_sorted_orders() -> None:
    client = TestClient(app)
    repository = agent_controller._order_repository
    repository.clear()

    repository.save(_make_order("d-old", "d1", OrderStatus.DELIVERY, 8))
    repository.save(_make_order("d-new", "d2", OrderStatus.DELIVERY, 2))
    repository.save(_make_order("c-old", "c1", OrderStatus.COORDINATE, 7))
    repository.save(_make_order("c-new", "c2", OrderStatus.COORDINATE, 1))
    repository.save(_make_order("b-old", "b1", OrderStatus.BACKYARD, 9))
    repository.save(_make_order("b-new", "b2", OrderStatus.BACKYARD, 3))

    response = client.get("/api/v1/orders/status-groups")

    assert response.status_code == 200
    body = response.json()
    assert [group["status"] for group in body] == ["DELIVERY", "COORDINATE", "BACKYARD"]
    assert [order["id"] for order in body[0]["orders"]] == ["d-new", "d-old"]
    assert [order["id"] for order in body[1]["orders"]] == ["c-new", "c-old"]
    assert [order["id"] for order in body[2]["orders"]] == ["b-new", "b-old"]


def test_v1_order_messages_returns_created_at_asc_and_status_event() -> None:
    client = TestClient(app)
    repository = agent_controller._order_repository
    repository.clear()

    order = _make_order("m1", "session-m1", OrderStatus.DELIVERY, 2)
    repository.save(order)

    agent_controller._conversation_service.add_order_message(
        order=order,
        role="user",
        content="依頼します",
        metadata={"intent": "NEW", "status_event": False, "order_status_before": None, "order_status_after": None},
    )
    agent_controller._conversation_service.add_order_message(
        order=order,
        role="assistant",
        content="ステータスを更新しました",
        metadata={
            "intent": "CONFIRM",
            "status_event": True,
            "order_status_before": "DELIVERY",
            "order_status_after": "COORDINATE",
        },
    )

    messages_response = client.get(f"/api/v1/orders/{order.id}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()

    created_at_list = [message["created_at"] for message in messages]
    assert created_at_list == sorted(created_at_list)
    assert any(message["metadata"].get("status_event") is True for message in messages)
