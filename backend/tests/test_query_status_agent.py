import asyncio
import json

from app.query_status_agent import QueryStatusAgent


class DummyFormatter:
    async def format_async(self, result_json: str) -> str:
        payload = json.loads(result_json)
        return f"formatted:{payload.get('status_code')}"


def test_query_status_agent_calls_n_number_tool():
    async def dummy_llm(system_prompt: str, user_prompt: str) -> str:
        return json.dumps(
            {
                "tool": "get_order_by_n_number",
                "arguments": {"n_number": "N123456789", "web_entry_id": None},
                "message": "",
            },
            ensure_ascii=False,
        )

    class DummyLookup:
        async def get_order_by_n_number(self, n_number: str) -> dict[str, object]:
            assert n_number == "N123456789"
            return {"ok": True, "status_code": 200}

        async def get_order_by_web_entry_id(self, web_entry_id: str) -> dict[str, object]:
            raise AssertionError("n number path should be called")

    agent = QueryStatusAgent(
        order_lookup_client=DummyLookup(),
        order_status_formatter=DummyFormatter(),
        llm_client_async=dummy_llm,
    )

    message = asyncio.run(agent.run("N123456789 の状況確認"))

    assert message == "formatted:200"
    assert agent.last_n_number == "N123456789"
    assert agent.last_web_entry_id is None


def test_query_status_agent_calls_web_entry_tool():
    async def dummy_llm(system_prompt: str, user_prompt: str) -> str:
        return json.dumps(
            {
                "tool": "get_order_by_web_entry_id",
                "arguments": {"n_number": "N123456789", "web_entry_id": "UN1234567890"},
                "message": "",
            },
            ensure_ascii=False,
        )

    class DummyLookup:
        async def get_order_by_web_entry_id(self, web_entry_id: str) -> dict[str, object]:
            assert web_entry_id == "UN1234567890"
            return {"ok": True, "status_code": 200}

        async def get_order_by_n_number(self, n_number: str) -> dict[str, object]:
            raise AssertionError("web entry path should be called")

    agent = QueryStatusAgent(
        order_lookup_client=DummyLookup(),
        order_status_formatter=DummyFormatter(),
        llm_client_async=dummy_llm,
    )

    message = asyncio.run(agent.run("UN1234567890 の現在状況"))

    assert message == "formatted:200"
    assert agent.last_web_entry_id == "UN1234567890"


def test_query_status_agent_returns_message_when_tool_is_null():
    async def dummy_llm(system_prompt: str, user_prompt: str) -> str:
        return json.dumps(
            {
                "tool": None,
                "arguments": {"n_number": None, "web_entry_id": None},
                "message": "識別子が見つからないため、N番号またはWebエントリIDを指定してください。",
            },
            ensure_ascii=False,
        )

    class DummyLookup:
        async def get_order_by_web_entry_id(self, web_entry_id: str) -> dict[str, object]:
            raise AssertionError("lookup should not be called")

        async def get_order_by_n_number(self, n_number: str) -> dict[str, object]:
            raise AssertionError("lookup should not be called")

    agent = QueryStatusAgent(
        order_lookup_client=DummyLookup(),
        order_status_formatter=DummyFormatter(),
        llm_client_async=dummy_llm,
    )

    message = asyncio.run(agent.run("進捗を確認したい"))

    assert message == "識別子が見つからないため、N番号またはWebエントリIDを指定してください。"
    assert agent.last_lookup_result is None
