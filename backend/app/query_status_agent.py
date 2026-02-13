from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.llm_client import generate_with_system_and_user_async
from app.order_lookup import MCPOrderLookupClient, OrderStatusFormatter

PROMPT_FILE_PATH = Path(__file__).parent / "prompts" / "query_status_router_agent_system_prompt.txt"
QUERY_STATUS_ROUTER_AGENT_SYSTEM_PROMPT = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
DEFAULT_IDENTIFIER_GUIDE_MESSAGE = "N番号（N+9桁）またはWebエントリID（UN+10桁）を本文に記載してください。"


class QueryStatusAgent:
    def __init__(
        self,
        order_lookup_client: MCPOrderLookupClient | None = None,
        order_status_formatter: OrderStatusFormatter | None = None,
        llm_client_async: Callable[[str, str], Any] = generate_with_system_and_user_async,
    ) -> None:
        self._order_lookup_client = order_lookup_client or MCPOrderLookupClient()
        self._order_status_formatter = order_status_formatter or OrderStatusFormatter()
        self._llm_client_async = llm_client_async
        self.last_lookup_result: dict[str, Any] | None = None
        self.last_n_number: str | None = None
        self.last_web_entry_id: str | None = None

    async def run(self, user_input: str) -> str:
        # Routerプロンプトで識別子抽出とツール選択（N番号/WebエントリID）を先に決定する。
        response_text = await self._llm_client_async(
            system_prompt=QUERY_STATUS_ROUTER_AGENT_SYSTEM_PROMPT,
            user_prompt=f"latest_input:\n{user_input}",
        )
        # LLM応答はJSON前提。崩れた場合はガイド文にフォールバックする。
        tool_call = self._safe_json_load(response_text)

        if not isinstance(tool_call, dict):
            tool_call = {"tool": None, "arguments": {}, "message": DEFAULT_IDENTIFIER_GUIDE_MESSAGE}

        tool_name = tool_call.get("tool")
        arguments = tool_call.get("arguments") if isinstance(tool_call.get("arguments"), dict) else {}
        message = tool_call.get("message") if isinstance(tool_call.get("message"), str) else None

        self.last_n_number = arguments.get("n_number") if isinstance(arguments.get("n_number"), str) else None
        self.last_web_entry_id = arguments.get("web_entry_id") if isinstance(arguments.get("web_entry_id"), str) else None

        if tool_name is None:
            self.last_lookup_result = None
            return message or DEFAULT_IDENTIFIER_GUIDE_MESSAGE

        # tool名と必要引数を対応付け、誤った呼び出しを早期に弾く。
        tool_map: dict[str, tuple[str, Callable[[str], Awaitable[dict[str, Any]]]]] = {
            "get_order_by_n_number": ("n_number", self._order_lookup_client.get_order_by_n_number),
            "get_order_by_web_entry_id": ("web_entry_id", self._order_lookup_client.get_order_by_web_entry_id),
        }

        selected = tool_map.get(tool_name)
        if selected is None:
            self.last_lookup_result = None
            return message or DEFAULT_IDENTIFIER_GUIDE_MESSAGE

        argument_key, tool_executor = selected
        argument_value = arguments.get(argument_key)
        if not isinstance(argument_value, str):
            self.last_lookup_result = None
            return message or DEFAULT_IDENTIFIER_GUIDE_MESSAGE

        if tool_name == "get_order_by_n_number":
            self.last_web_entry_id = None

        # 取得結果は会話継続のためインスタンスに保持し、整形Agentへ受け渡す。
        lookup_result = await tool_executor(argument_value)
        self.last_lookup_result = lookup_result
        lookup_result_json = json.dumps(lookup_result, ensure_ascii=False)
        return await self._order_status_formatter.format_async(lookup_result_json)

    def _safe_json_load(self, response_text: str) -> dict[str, Any]:
        fallback = {"tool": None, "arguments": {}, "message": DEFAULT_IDENTIFIER_GUIDE_MESSAGE}
        try:
            parsed = json.loads(response_text)
            return parsed if isinstance(parsed, dict) else fallback
        except json.JSONDecodeError:
            pass

        decoder = json.JSONDecoder()
        for index, char in enumerate(response_text):
            if char != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(response_text[index:])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        return fallback
