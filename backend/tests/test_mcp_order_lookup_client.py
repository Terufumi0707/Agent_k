import json

from app.order_lookup.mcp_order_lookup_client import MCPOrderLookupClient


class DummyContentItem:
    def __init__(self, text: str) -> None:
        self.text = text


class DummyContentItemWithJson:
    def __init__(self, json_payload):
        self.json = json_payload


class DummyResponseWithContent:
    def __init__(self, content):
        self.content = content


class DummyResponseWithModelDump:
    def model_dump(self):
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"ok": True, "status_code": 200, "payload": {"id": "x"}}, ensure_ascii=False),
                }
            ]
        }


def test_to_dict_accepts_plain_json_string_response():
    client = MCPOrderLookupClient(base_url="http://example.com", timeout_seconds=1)

    result = client._to_dict('{"ok": true, "status_code": 200, "payload": {"order_id": "1"}}')

    assert result["ok"] is True
    assert result["status_code"] == 200


def test_to_dict_parses_markdown_fenced_json_in_content():
    client = MCPOrderLookupClient(base_url="http://example.com", timeout_seconds=1)
    response = DummyResponseWithContent(
        [DummyContentItem('```json\n{"ok": true, "status_code": 200, "payload": {"order_id": "2"}}\n```')]
    )

    result = client._to_dict(response)

    assert result["ok"] is True
    assert result["payload"]["order_id"] == "2"


def test_to_dict_prefers_structured_content_in_dict_response():
    client = MCPOrderLookupClient(base_url="http://example.com", timeout_seconds=1)

    result = client._to_dict(
        {
            "structured_content": {"ok": True, "status_code": 200, "payload": {"order_id": "3"}},
            "content": [{"type": "text", "text": "ignored"}],
        }
    )

    assert result["ok"] is True
    assert result["payload"]["order_id"] == "3"


def test_to_dict_uses_model_dump_when_available():
    client = MCPOrderLookupClient(base_url="http://example.com", timeout_seconds=1)

    result = client._to_dict(DummyResponseWithModelDump())

    assert result["ok"] is True
    assert result["status_code"] == 200


def test_to_dict_parses_python_dict_string_from_content_text():
    client = MCPOrderLookupClient(base_url="http://example.com", timeout_seconds=1)
    response = DummyResponseWithContent(
        [DummyContentItem("{'ok': True, 'status_code': 200, 'payload': {'order_id': '4'}}")]
    )

    result = client._to_dict(response)

    assert result["ok"] is True
    assert result["payload"]["order_id"] == "4"


def test_to_dict_parses_json_field_from_content_item():
    client = MCPOrderLookupClient(base_url="http://example.com", timeout_seconds=1)
    response = DummyResponseWithContent(
        [DummyContentItemWithJson({"ok": True, "status_code": 200, "payload": {"order_id": "5"}})]
    )

    result = client._to_dict(response)

    assert result["ok"] is True
    assert result["payload"]["order_id"] == "5"


def test_to_dict_parses_result_field_from_dict_response():
    client = MCPOrderLookupClient(base_url="http://example.com", timeout_seconds=1)

    result = client._to_dict({"result": {"ok": True, "status_code": 200, "payload": {"order_id": "6"}}})

    assert result["ok"] is True
    assert result["payload"]["order_id"] == "6"
