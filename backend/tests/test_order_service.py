from app.repositories.order_repository import InMemoryOrderRepository
from app.services.order_service import OrderService


def test_update_summary_uses_llm_output() -> None:
    repository = InMemoryOrderRepository()

    def stub_llm(system_prompt: str, user_prompt: str) -> str:
        assert "通信事業者の工事日程調整" in system_prompt
        assert "ユーザー発話:" in user_prompt
        assert "アシスタント応答:" in user_prompt
        return "通信事業者工事の訪問日時を顧客希望に合わせて再調整"

    service = OrderService(repository=repository, llm_client=stub_llm)
    order = service.create_if_not_exists(session_id="session-for-summary")

    service.update_summary(
        session_id=order.session_id,
        user_input="工事を来週火曜午前に変更できますか",
        assistant_message="通信事業者へ空き枠確認のうえ折り返します",
    )

    saved = repository.find_by_session_id(order.session_id)
    assert saved is not None
    assert saved.summary == "通信事業者工事の訪問日時を顧客希望に合わせて再調整"


def test_update_summary_falls_back_when_llm_returns_empty() -> None:
    repository = InMemoryOrderRepository()
    service = OrderService(repository=repository, llm_client=lambda _s, _u: "")
    order = service.create_if_not_exists(session_id="session-summary-fallback")

    service.update_summary(
        session_id=order.session_id,
        user_input="候補日は水曜午後と金曜午前です",
        assistant_message="通信事業者へ候補日を連携して回答待ちです",
    )

    saved = repository.find_by_session_id(order.session_id)
    assert saved is not None
    assert saved.summary.startswith("通信事業者工事の日程調整:")
