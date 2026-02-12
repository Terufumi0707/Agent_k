from __future__ import annotations

import asyncio
import json
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
            return self._to_dict(response)

        return await asyncio.wait_for(_invoke(), timeout=self._timeout_seconds)

    def _to_dict(self, response: Any) -> dict[str, Any]:
        if isinstance(response, dict):
            return response

        if hasattr(response, "data") and isinstance(response.data, dict):
            return response.data

        if hasattr(response, "structured_content") and isinstance(response.structured_content, dict):
            return response.structured_content

        if hasattr(response, "content") and isinstance(response.content, list):
            for item in response.content:
                text = getattr(item, "text", None)
                if isinstance(text, str):
                    try:
                        parsed = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(parsed, dict):
                        return parsed

        return {
            "ok": False,
            "status_code": 500,
            "payload": {"error": {"code": "INVALID_MCP_RESPONSE", "message": "Invalid MCP response."}},
        }
