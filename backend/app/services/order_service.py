from __future__ import annotations

from typing import Callable

from app.domain.order import Order, OrderStatus
from app.llm_client import generate_with_system_and_user
from app.repositories.order_repository import OrderRepository

SUMMARY_SYSTEM_PROMPT = (
    "あなたは通信事業者の工事日程調整の案件管理アシスタントです。"
    "ユーザー発話とアシスタント応答を1行で要約してください。"
    "出力は50文字以内、日本語、体言止め、機微情報は含めない。"
)


def _truncate_text(value: str, limit: int = 70) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1]}…"


class InvalidOrderStatusTransitionError(ValueError):
    pass


class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        llm_client: Callable[[str, str], str] = generate_with_system_and_user,
    ) -> None:
        self._repository = repository
        self._llm_client = llm_client

    def create_if_not_exists(self, session_id: str) -> Order:
        existing_order = self._repository.find_by_session_id(session_id)
        if existing_order is not None:
            return existing_order

        order = Order.create(session_id=session_id, current_status=OrderStatus.DELIVERY)
        self._repository.save(order)
        return order

    def move_to_coordinate(self, session_id: str) -> tuple[OrderStatus, OrderStatus]:
        order = self._repository.find_by_session_id(session_id)
        if order is None:
            raise KeyError(session_id)

        if order.current_status != OrderStatus.DELIVERY:
            raise InvalidOrderStatusTransitionError(
                f"invalid transition: {order.current_status} -> {OrderStatus.COORDINATE}"
            )

        before = order.current_status
        order.current_status = OrderStatus.COORDINATE
        self._repository.save(order)
        return before, order.current_status

    def move_to_backyard(self, session_id: str) -> None:
        order = self._repository.find_by_session_id(session_id)
        if order is None:
            raise KeyError(session_id)

        order.current_status = OrderStatus.BACKYARD
        self._repository.save(order)

    def list_orders(self, limit: int = 100, offset: int = 0) -> list[Order]:
        return self._repository.list_orders(sort="updated_at_desc", limit=limit, offset=offset)

    def list_orders_legacy(self, status: OrderStatus | None = None) -> list[Order]:
        if status is None:
            return self._repository.list_all()
        return self._repository.find_by_status(status)

    def list_orders_by_status_group(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        groups: list[dict[str, object]] = []
        for status in [OrderStatus.DELIVERY, OrderStatus.COORDINATE, OrderStatus.BACKYARD]:
            groups.append(
                {
                    "status": status,
                    "orders": self._repository.list_orders_by_status(
                        status=status,
                        sort="updated_at_desc",
                        limit=limit,
                        offset=offset,
                    ),
                }
            )
        return groups

    def get_by_session_id(self, session_id: str) -> Order | None:
        return self._repository.find_by_session_id(session_id)

    def get_by_id(self, order_id: str) -> Order | None:
        return self._repository.find_by_id(order_id)

    def update_summary(self, session_id: str, user_input: str, assistant_message: str) -> None:
        order = self._repository.find_by_session_id(session_id)
        if order is None:
            return

        user_prompt = (
            "以下を要約してください。\n"
            f"ユーザー発話: {user_input}\n"
            f"アシスタント応答: {assistant_message}"
        )
        llm_summary = self._llm_client(SUMMARY_SYSTEM_PROMPT, user_prompt)
        normalized_summary = " ".join(llm_summary.split())

        if normalized_summary:
            order.summary = _truncate_text(normalized_summary, limit=50)
        else:
            user_digest = _truncate_text(user_input, limit=20)
            assistant_digest = _truncate_text(assistant_message, limit=20)
            order.summary = (
                f"通信事業者工事の日程調整: 依頼『{user_digest}』/ 対応『{assistant_digest}』"
            )

        self._repository.save(order)

    def save_lookup_identifiers(self, session_id: str, n_number: str | None, web_entry_id: str | None) -> None:
        order = self._repository.find_by_session_id(session_id)
        if order is None:
            return
        if n_number is not None:
            order.n_number = n_number
        if web_entry_id is not None:
            order.web_entry_id = web_entry_id
        self._repository.save(order)
