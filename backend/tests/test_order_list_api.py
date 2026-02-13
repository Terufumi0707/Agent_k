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
        summary=f"通信事業者工事の日程調整 {order_id}",
        current_status=status,
        created_at=base - timedelta(minutes=minutes + 1),
        updated_at=base - timedelta(minutes=minutes),
    )




def _reset_default_seed_data() -> None:
    agent_controller._order_repository.seed_defaults()
    agent_controller._conversation_repository = agent_controller.InMemoryConversationRepository()
    agent_controller._conversation_service = agent_controller.ConversationService(repository=agent_controller._conversation_repository)
    agent_controller._conversation_service.seed_order_histories(agent_controller._order_repository.list_all())
    agent_controller._order_query_service = agent_controller.OrderQueryService(
        order_service=agent_controller._order_service,
        conversation_service=agent_controller._conversation_service,
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
    payload = response.json()
    ids = [item["id"] for item in payload]
    assert ids == ["o2", "o3", "o1"]
    assert all("通信事業者工事の日程調整" in item["summary"] for item in payload)


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


def test_seeded_demo_messages_for_delivery_orders() -> None:
    _reset_default_seed_data()
    client = TestClient(app)

    response_001 = client.get("/api/v1/orders/order-delivery-001/messages")
    response_002 = client.get("/api/v1/orders/order-delivery-002/messages")

    assert response_001.status_code == 200
    assert response_002.status_code == 200

    messages_001 = response_001.json()
    messages_002 = response_002.json()

    assert len(messages_001) >= 5
    assert len(messages_002) >= 3

    assert [message["role"] for message in messages_001[:5]] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "system",
    ]
    assert [message["role"] for message in messages_002[:3]] == ["user", "assistant", "assistant"]

    status_events_001 = [message for message in messages_001 if message["metadata"].get("status_event") is True]
    status_events_002 = [message for message in messages_002 if message["metadata"].get("status_event") is True]

    assert any(message["metadata"].get("order_status_before") == "COORDINATE" for message in status_events_001)
    assert any(message["metadata"].get("order_status_after") == "DELIVERY" for message in status_events_001)
    assert any(message["metadata"].get("order_status_before") == "COORDINATE" for message in status_events_002)
    assert any(message["metadata"].get("order_status_after") == "DELIVERY" for message in status_events_002)


def test_all_default_orders_have_histories_and_last_status_matches_current() -> None:
    _reset_default_seed_data()
    client = TestClient(app)

    orders_response = client.get("/api/v1/orders")
    assert orders_response.status_code == 200
    orders = orders_response.json()

    assert len(orders) >= 9

    for order in orders:
        messages_response = client.get(f"/api/v1/orders/{order['id']}/messages")
        assert messages_response.status_code == 200
        messages = messages_response.json()
        assert len(messages) >= 3

        last_message = messages[-1]
        assert last_message["metadata"].get("order_status_after") == order["current_status"]
