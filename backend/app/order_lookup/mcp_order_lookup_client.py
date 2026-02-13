from __future__ import annotations

import asyncio
import ast
import json
from collections.abc import Sequence
from typing import Any

from app.settings import get_http_timeout_seconds, get_order_lookup_mcp_base_url


class MCPOrderLookupClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._base_url = base_url or get_order_lookup_mcp_base_url()
        self._timeout_seconds = timeout_seconds or get_http_timeout_seconds()

    async def get_order_by_n_number(self, n_number: str) -> dict[str, Any]:
        return await self._call_tool("get_order_by_n_number", {"n_number": n_number})

    async def get_order_by_web_entry_id(self, web_entry_id: str) -> dict[str, Any]:
        return await self._call_tool("get_order_by_web_entry_id", {"web_entry_id": web_entry_id})

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async def _invoke() -> dict[str, Any]:
            try:
                from fastmcp import Client
            except ImportError:
                return {
                    "ok": False,
                    "status_code": 500,
                    "payload": {
                        "error": {
                            "code": "MCP_CLIENT_NOT_AVAILABLE",
                            "message": "fastmcp is not installed.",
                        }
                    },
                }

            async with Client(self._base_url) as client:
                response = await client.call_tool(tool_name, arguments)
            print(response)
            return self._to_dict(response)

        return await asyncio.wait_for(_invoke(), timeout=self._timeout_seconds)

    def _to_dict(self, response: Any) -> dict[str, Any]:
        if isinstance(response, str):
            parsed = self._extract_json_dict(response)
            if parsed is not None:
                return parsed

        if isinstance(response, Sequence) and not isinstance(response, (str, bytes)):
            parsed_from_response_list = self._parse_content_list(response)
            if parsed_from_response_list is not None:
                return parsed_from_response_list

        if isinstance(response, dict):
            structured_content = response.get("structured_content") or response.get("structuredContent")
            parsed_structured_content = self._extract_dict_value(structured_content)
            if parsed_structured_content is not None:
                return parsed_structured_content

            content = response.get("content")
            if isinstance(content, Sequence) and not isinstance(content, (str, bytes)):
                parsed_from_content = self._parse_content_list(content)
                if parsed_from_content is not None:
                    return parsed_from_content

            result = response.get("result")
            if result is not None:
                parsed_result = self._extract_dict_value(result)
                if parsed_result is not None:
                    return parsed_result

            return response

        if hasattr(response, "data"):
            parsed_data = self._extract_dict_value(response.data)
            if parsed_data is not None:
                return parsed_data

        if hasattr(response, "structured_content"):
            parsed_structured_content = self._extract_dict_value(response.structured_content)
            if parsed_structured_content is not None:
                return parsed_structured_content

        if hasattr(response, "structuredContent"):
            parsed_structured_content = self._extract_dict_value(response.structuredContent)
            if parsed_structured_content is not None:
                return parsed_structured_content

        if hasattr(response, "content") and isinstance(response.content, Sequence) and not isinstance(response.content, (str, bytes)):
            parsed_from_content = self._parse_content_list(response.content)
            if parsed_from_content is not None:
                return parsed_from_content

        model_dump = getattr(response, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump()
            if isinstance(dumped, dict):
                return self._to_dict(dumped)

        return {
            "ok": False,
            "status_code": 500,
            "payload": {"error": {"code": "INVALID_MCP_RESPONSE", "message": "Invalid MCP response."}},
        }

    def _parse_content_list(self, content_items: Sequence[Any]) -> dict[str, Any] | None:
        for item in content_items:
            if isinstance(item, dict):
                parsed = self._extract_dict_value(item.get("json"))
                if parsed is not None:
                    return parsed
                text = item.get("text")
            else:
                json_content = getattr(item, "json", None)
                parsed = self._extract_dict_value(json_content)
                if parsed is not None:
                    return parsed
                text = getattr(item, "text", None)
            if not isinstance(text, str):
                continue
            parsed = self._extract_json_dict(text)
            if parsed is not None:
                return parsed
        return None

    def _extract_dict_value(self, value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            return self._extract_json_dict(value)

        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump()
            if isinstance(dumped, dict):
                return dumped

        return None

    def _extract_json_dict(self, text: str) -> dict[str, Any] | None:
        # MCPサーバー実装によっては ```json ... ``` 形式で返ることがあるため除去する。
        normalized = text.strip()
        if normalized.startswith("```"):
            lines = normalized.splitlines()
            if len(lines) >= 3:
                normalized = "\n".join(lines[1:-1]).strip()

        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(normalized)
            except (ValueError, SyntaxError):
                return None

        if isinstance(parsed, dict):
            return parsed
        return None
