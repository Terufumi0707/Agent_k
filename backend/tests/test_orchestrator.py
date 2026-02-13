import json

import app.orchestrator as orchestrator
from app.intent_classifier import IntentClassification
from app.repositories.order_repository import InMemoryOrderRepository
from app.services.order_status_service import OrderStatusService
from app.session_store import InMemorySessionStore, SessionState


def test_orchestrator_run_executes_full_pipeline_and_returns_formatter_result(monkeypatch):
    captured: list[tuple[str, str]] = []

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured.append((system_prompt, user_prompt))
        if system_prompt == orchestrator.AGENT_SYSTEM_PROMPT:
            return '{"extracted": true}'
        if system_prompt == orchestrator.JUDGE_AGENT_SYSTEM_PROMPT:
            assert user_prompt == '{"extracted": true}'
            return '{"judge": "ok"}'
        if system_prompt == orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT:
            assert 'extracted_result:\n{"extracted": true}' in user_prompt
            assert 'judge_result:\n{"judge": "ok"}' in user_prompt
            return "display-message"
        raise AssertionError("unexpected system prompt")

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    class DummyIntentClassifier:
        def __init__(self) -> None:
            self.count = 0

        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            self.count += 1
            assert user_input == "PlaceHolderのRequest"
            assert session_state is None
            return IntentClassification(intent="NEW", confidence=0.8, reason="新規入力")

    dummy_classifier = DummyIntentClassifier()
    monkeypatch.setattr(
        orchestrator.CreateEntryService,
        "route_query_status",
        lambda self, user_input: {
            "n_number": "N123456789",
            "web_entry_id": "UN1234567890",
            "action": "LOOKUP_BY_WEB_ENTRY_ID",
            "reason": "both",
        },
    )

    store = InMemorySessionStore()
    monkeypatch.setattr(
        orchestrator.CreateEntryService,
        "route_query_status",
        lambda self, user_input: {
            "n_number": None,
            "web_entry_id": None,
            "action": "NEED_IDENTIFIER",
            "reason": "missing",
        },
    )

    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=store,
        intent_classifier=dummy_classifier,
    ).run("PlaceHolderのRequest")

    assert dummy_classifier.count == 1
    assert len(captured) == 3
    assert captured[0] == (orchestrator.AGENT_SYSTEM_PROMPT, "PlaceHolderのRequest")
    assert captured[1] == (orchestrator.JUDGE_AGENT_SYSTEM_PROMPT, '{"extracted": true}')
    assert captured[2][0] == orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT
    assert result == "display-message"
    assert isinstance(session_id, str)
    state = store.get(session_id)
    assert state is not None
    assert state.extracted_json == '{"extracted": true}'
    assert state.extracted_json_raw == '{"extracted": true}'


def test_orchestrator_system_prompt_loaded_from_file():
    file_prompt = orchestrator.PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
    assert orchestrator.AGENT_SYSTEM_PROMPT == file_prompt


def test_orchestrator_run_judge_calls_agent_once_with_judge_system_prompt(monkeypatch):
    captured = {"count": 0, "system_prompt": "", "user_prompt": ""}

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured["count"] += 1
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "judge-agent-result"

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    result = orchestrator.CreateEntryOrchestrator()._run_judge("抽出JSON")

    assert captured["count"] == 1
    assert captured["system_prompt"] == orchestrator.JUDGE_AGENT_SYSTEM_PROMPT
    assert captured["user_prompt"] == "抽出JSON"
    assert result == "judge-agent-result"


def test_judge_system_prompt_loaded_from_file():
    file_prompt = orchestrator.JUDGE_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
    assert orchestrator.JUDGE_AGENT_SYSTEM_PROMPT == file_prompt


def test_orchestrator_build_user_message_calls_formatter_agent(monkeypatch):
    captured = {"count": 0, "system_prompt": "", "user_prompt": ""}

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured["count"] += 1
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "display-message"

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    extracted_result = {"construction_types": [{"normalized_type": "切替工事"}]}
    judge_result = {"judge_result": {"status": "CONFIRM"}}

    result = orchestrator.CreateEntryOrchestrator()._build_user_message(
        extracted_json=json.dumps(extracted_result, ensure_ascii=False),
        judge_json=json.dumps(judge_result, ensure_ascii=False),
    )

    assert captured["count"] == 1
    assert captured["system_prompt"] == orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT
    assert "extracted_result:\n" in captured["user_prompt"]
    assert "judge_result:\n" in captured["user_prompt"]
    assert json.dumps(extracted_result, ensure_ascii=False) in captured["user_prompt"]
    assert json.dumps(judge_result, ensure_ascii=False) in captured["user_prompt"]
    assert result == "display-message"


def test_formatter_system_prompt_loaded_from_file():
    file_prompt = orchestrator.FORMATTER_PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
    assert orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT == file_prompt


def test_generate_patch_returns_parsed_patches(monkeypatch):
    store = InMemorySessionStore()
    store.save(
        "session-123",
        SessionState(
            extracted_json='{"preferred_dates": [{"priority": 1, "date": "2026-04-01"}]}',
            judge_result="{}",
            user_view_message="",
            intent_result="{}",
            pending_patch=None,
            preview_extracted_json=None,
        ),
    )

    def mock_generate(user_change_input: str, extracted_json: str) -> dict[str, object]:
        assert user_change_input == "希望日を変えてください"
        assert extracted_json == '{"preferred_dates": [{"priority": 1, "date": "2026-04-01"}]}'
        return {
            "patches": [
                {
                    "operation": "update",
                    "target": "preferred_dates[priority=1].date",
                    "value": "2026-04-02",
                    "reason": "ユーザーが希望日を変更すると明示したため",
                }
            ]
        }

    patch_generator = orchestrator.PatchGenerator(system_prompt="prompt")
    monkeypatch.setattr(patch_generator, "generate", mock_generate)

    result = orchestrator.CreateEntryOrchestrator(
        session_store=store,
        patch_generator=patch_generator,
    )._generate_patch("希望日を変えてください", session_state=store.get("session-123"))

    assert result == {
        "patches": [
            {
                "operation": "update",
                "target": "preferred_dates[priority=1].date",
                "value": "2026-04-02",
                "reason": "ユーザーが希望日を変更すると明示したため",
            }
        ]
    }


def test_orchestrator_change_intent_returns_change_preview_message(monkeypatch):
    store = InMemorySessionStore()
    store.save(
        "session-456",
        SessionState(
            extracted_json='{"preferred_dates": [{"priority": 1, "date": "2026-04-01"}]}',
            judge_result="{}",
            user_view_message="",
            intent_result="{}",
            pending_patch=None,
            preview_extracted_json=None,
        ),
    )

    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            assert user_input == "希望日を変えてください"
            assert session_state is not None
            return IntentClassification(intent="CHANGE", confidence=0.9, reason="変更依頼")

    captured: list[tuple[str, str]] = []

    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        captured.append((system_prompt, user_prompt))
        if system_prompt == orchestrator.CHANGE_PREVIEW_AGENT_SYSTEM_PROMPT:
            assert "extracted_json:\n" in user_prompt
            assert "user_change_input:\n希望日を変えてください" in user_prompt
            return '{"preferred_dates": [{"priority": 1, "date": "2026-04-02"}]}'
        if system_prompt == orchestrator.CHANGE_PREVIEW_FORMATTER_AGENT_SYSTEM_PROMPT:
            assert "preview_extracted_json:\n" in user_prompt
            return "変更後の内容の要約"
        raise AssertionError("unexpected system prompt")

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=store,
        intent_classifier=DummyIntentClassifier(),
    ).run("希望日を変えてください", session_id="session-456")

    assert result == (
        "変更後の内容の要約\n\nこの内容でよろしければ確定してください。\nさらに変更があれば指示してください。"
    )
    assert session_id == "session-456"
    assert len(captured) == 2


def test_orchestrator_change_intent_without_session_returns_missing_target_message():
    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            assert user_input == "変更してください"
            assert session_state is None
            return IntentClassification(intent="CHANGE", confidence=0.9, reason="変更依頼")

    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=InMemorySessionStore(),
        intent_classifier=DummyIntentClassifier(),
    ).run("変更してください")

    assert result == "変更対象となる情報がありません。"
    assert isinstance(session_id, str)


class DummyOrderStatusFormatter:
    def format(self, result_json: str) -> str:
        payload = json.loads(result_json)
        return f"formatted:{payload.get('status_code')}"


def test_orchestrator_query_status_calls_web_entry_lookup_and_formats_result(monkeypatch):
    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            return IntentClassification(intent="QUERY_STATUS", confidence=0.9, reason="照会")

    class DummyOrderLookupClient:
        async def get_order_by_n_number(self, n_number: str) -> dict[str, object]:
            raise AssertionError("web_entry_id should be preferred")

        async def get_order_by_web_entry_id(self, web_entry_id: str) -> dict[str, object]:
            assert web_entry_id == "UN1234567890"
            return {"ok": True, "status_code": 200, "payload": {"identifiers": {"web_entry_id": web_entry_id}}}

    monkeypatch.setattr(
        orchestrator.CreateEntryService,
        "route_query_status",
        lambda self, user_input: {
            "n_number": "N123456789",
            "web_entry_id": "UN1234567890",
            "action": "LOOKUP_BY_WEB_ENTRY_ID",
            "reason": "both",
        },
    )

    store = InMemorySessionStore()
    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=store,
        intent_classifier=DummyIntentClassifier(),
        order_lookup_client=DummyOrderLookupClient(),
        order_status_formatter=DummyOrderStatusFormatter(),
    ).run("N123456789 と UN1234567890 の現在状況を教えて")

    assert result == "formatted:200"
    state = store.get(session_id)
    assert state is not None
    assert state.last_lookup is not None
    assert '"web_entry_id": "UN1234567890"' in state.last_lookup


def test_orchestrator_query_status_without_identifier_returns_guide_message(monkeypatch):
    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            return IntentClassification(intent="QUERY_STATUS", confidence=0.9, reason="照会")

    monkeypatch.setattr(
        orchestrator.CreateEntryService,
        "route_query_status",
        lambda self, user_input: {
            "n_number": None,
            "web_entry_id": None,
            "action": "NEED_IDENTIFIER",
            "reason": "missing",
        },
    )

    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=InMemorySessionStore(),
        intent_classifier=DummyIntentClassifier(),
    ).run("現在の工事予定を確認したい")

    assert result == "N番号（N+9桁）またはWebエントリID（UN+10桁）を本文に記載してください。"
    assert isinstance(session_id, str)


def test_orchestrator_query_status_formats_error_response(monkeypatch):
    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            return IntentClassification(intent="QUERY_STATUS", confidence=0.9, reason="照会")

    class DummyOrderLookupClient:
        async def get_order_by_n_number(self, n_number: str) -> dict[str, object]:
            assert n_number == "N123456789"
            return {
                "ok": False,
                "status_code": 404,
                "payload": {"error": {"message": "not found"}},
            }

        async def get_order_by_web_entry_id(self, web_entry_id: str) -> dict[str, object]:
            raise AssertionError("n_number path should be called")

    monkeypatch.setattr(
        orchestrator.CreateEntryService,
        "route_query_status",
        lambda self, user_input: {
            "n_number": "N123456789",
            "web_entry_id": None,
            "action": "LOOKUP_BY_N_NUMBER",
            "reason": "n-only",
        },
    )

    result, _ = orchestrator.CreateEntryOrchestrator(
        session_store=InMemorySessionStore(),
        intent_classifier=DummyIntentClassifier(),
        order_lookup_client=DummyOrderLookupClient(),
        order_status_formatter=DummyOrderStatusFormatter(),
    ).run("N123456789 のステータス確認")

    assert result == "formatted:404"


def test_orchestrator_new_intent_sets_order_status_delivery(monkeypatch):
    def mock_generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
        if system_prompt == orchestrator.AGENT_SYSTEM_PROMPT:
            return '{"extracted": true}'
        if system_prompt == orchestrator.JUDGE_AGENT_SYSTEM_PROMPT:
            return '{"judge": "ok"}'
        if system_prompt == orchestrator.FORMATTER_AGENT_SYSTEM_PROMPT:
            return "display-message"
        raise AssertionError("unexpected system prompt")

    monkeypatch.setattr(orchestrator, "generate_with_system_and_user", mock_generate_with_system_and_user)

    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            return IntentClassification(intent="NEW", confidence=0.8, reason="新規入力")

    order_repository = InMemoryOrderRepository()
    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=InMemorySessionStore(),
        intent_classifier=DummyIntentClassifier(),
        order_repository=order_repository,
    ).run("PlaceHolderのRequest")

    saved_order = order_repository.get_by_id(session_id)
    assert result == "display-message"
    assert saved_order is not None
    assert saved_order.current_status.value == "DELIVERY"


def test_orchestrator_confirm_intent_updates_order_status_to_coordinate():
    class DummyIntentClassifier:
        def classify(self, user_input: str, session_state: SessionState | None = None) -> IntentClassification:
            return IntentClassification(intent="CONFIRM", confidence=0.9, reason="確定")

    order_repository = InMemoryOrderRepository()
    order_status_service = OrderStatusService(order_repository)
    order_status_service.create_new_order(order_id="session-999")

    result, session_id = orchestrator.CreateEntryOrchestrator(
        session_store=InMemorySessionStore(),
        intent_classifier=DummyIntentClassifier(),
        order_status_service=order_status_service,
    ).run("確定です", session_id="session-999")

    saved_order = order_repository.get_by_id("session-999")
    assert session_id == "session-999"
    assert result == "内容を確定しました。ありがとうございます。"
    assert saved_order is not None
    assert saved_order.current_status.value == "COORDINATE"
