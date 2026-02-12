from __future__ import annotations

import os
import re
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

N_NUMBER_PATTERN = re.compile(r"^N[0-9]{9}$")
WEB_ENTRY_ID_PATTERN = re.compile(r"^UN[0-9]{10}$")

API_BASE_URL = os.getenv("ORDER_LOOKUP_API_BASE_URL", "http://localhost:8001")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("ORDER_LOOKUP_API_TIMEOUT_SECONDS", "5"))

mcp = FastMCP("order-lookup-mcp")


async def _get(path: str) -> dict[str, Any]:
    url = f"{API_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(url)

    try:
        payload = response.json()
    except ValueError:
        payload = {"error": {"code": "INVALID_RESPONSE", "message": response.text, "trace_id": ""}}

    if response.status_code >= 400:
        return {
            "ok": False,
            "status_code": response.status_code,
            "payload": payload,
        }

    return {
        "ok": True,
        "status_code": response.status_code,
        "payload": payload,
    }


@mcp.tool()
async def get_order_by_n_number(n_number: str) -> dict[str, Any]:
    """N番号でオーダー状況照会APIを呼び出します。"""
    if not N_NUMBER_PATTERN.match(n_number):
        return {
            "ok": False,
            "status_code": 400,
            "payload": {
                "error": {
                    "code": "INVALID_IDENTIFIER",
                    "message": "n_number の形式が不正です",
                    "trace_id": "",
                }
            },
        }

    return await _get(f"/v1/orders/by-n-number/{n_number}")


@mcp.tool()
async def get_order_by_web_entry_id(web_entry_id: str) -> dict[str, Any]:
    """WebエントリIDでオーダー状況照会APIを呼び出します。"""
    if not WEB_ENTRY_ID_PATTERN.match(web_entry_id):
        return {
            "ok": False,
            "status_code": 400,
            "payload": {
                "error": {
                    "code": "INVALID_IDENTIFIER",
                    "message": "web_entry_id の形式が不正です",
                    "trace_id": "",
                }
            },
        }

    return await _get(f"/v1/orders/{web_entry_id}")


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "9000"))

    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=transport, host=host, port=port)
