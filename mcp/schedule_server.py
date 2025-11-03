"""Minimal MCP server exposing the ``schedule.change`` tool via stdio."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from typing import Any, Dict

from backend.domain.schedule_change.entities import (
    ScheduleChangeRequest,
    ScheduleChangeResponse,
)
from mock_api.schedule_change_service import handle_schedule_change_request


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

TOOL_NAME = "schedule.change"


@dataclass(frozen=True)
class ToolRequest:
    """Parsed representation of a tool invocation from the MCP client."""

    method: str
    tool: str
    args: Dict[str, Any]
    request_id: str


@dataclass(frozen=True)
class ToolResponse:
    """Structured MCP tool response."""

    result: Dict[str, Any] | None
    error: Dict[str, Any] | None
    request_id: str

    def to_json(self) -> str:
        """Serialize the response as a single-line JSON string."""

        payload: Dict[str, Any] = {"id": self.request_id}

        if self.error is not None:
            payload["error"] = self.error
        elif self.result is not None:
            payload["result"] = self.result
        else:
            payload["result"] = None

        return json.dumps(payload, ensure_ascii=False)


def _parse_request(raw: str) -> ToolRequest:
    """Convert a raw JSON string into a :class:`ToolRequest`."""

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
        raise ValueError(f"invalid JSON payload: {exc}") from exc

    method = payload.get("method")
    tool = payload.get("tool")
    args = payload.get("args")
    request_id = payload.get("id")

    if not isinstance(method, str) or not isinstance(tool, str):
        raise ValueError("method and tool must be provided as strings")

    if not isinstance(args, dict):
        raise ValueError("args must be an object")

    if not isinstance(request_id, str):
        raise ValueError("id must be provided as a string")

    return ToolRequest(method=method, tool=tool, args=args, request_id=request_id)


def _handle_schedule_change(args: Dict[str, Any]) -> ScheduleChangeResponse:
    """Invoke the mock schedule change service using the provided arguments."""

    entry_id = args.get("entry_id")
    prompt = args.get("prompt")
    requester = args.get("requester")
    reason = args.get("reason")

    if not isinstance(entry_id, str) or not isinstance(prompt, str):
        raise ValueError("entry_id and prompt must be provided as strings")

    if requester is not None and not isinstance(requester, str):
        raise ValueError("requester must be either a string or null")

    if reason is not None and not isinstance(reason, str):
        raise ValueError("reason must be either a string or null")

    payload = ScheduleChangeRequest(
        entry_id=entry_id,
        prompt=prompt,
        requester=requester,
        reason=reason,
    )
    logger.info(
        "mcp_schedule_server_call tool=%s entry_id=%s", TOOL_NAME, payload.entry_id
    )
    return handle_schedule_change_request(payload)


def _build_success_response(
    response: ScheduleChangeResponse, request_id: str
) -> ToolResponse:
    return ToolResponse(
        result={"status": response.status, "message": response.message},
        error=None,
        request_id=request_id,
    )


def _build_error_response(message: str, request_id: str) -> ToolResponse:
    return ToolResponse(result=None, error={"message": message}, request_id=request_id)


def _dispatch(request: ToolRequest) -> ToolResponse:
    """Route the incoming request to the appropriate tool handler."""

    if request.method != "tool.call":
        return _build_error_response(
            f"unsupported method: {request.method}", request.request_id
        )

    if request.tool != TOOL_NAME:
        return _build_error_response(
            f"unsupported tool: {request.tool}", request.request_id
        )

    try:
        response = _handle_schedule_change(request.args)
    except Exception as exc:  # pragma: no cover - exercised via error paths
        logger.exception("tool execution failed: %s", exc)
        return _build_error_response(str(exc), request.request_id)

    return _build_success_response(response, request.request_id)


def serve() -> None:
    """Start the stdio MCP server and process requests sequentially."""

    logger.info("schedule MCP server started. waiting for requests...")

    for raw_line in sys.stdin:
        line = raw_line.strip()

        if not line:
            continue

        try:
            request = _parse_request(line)
            response = _dispatch(request)
        except Exception as exc:  # pragma: no cover - robust error handling
            logger.exception("failed to process request: %s", exc)
            # Attempt to extract request id if present.
            try:
                payload = json.loads(line)
                request_id = payload.get("id", "unknown")
            except Exception:  # pragma: no cover - best effort fallback
                request_id = "unknown"
            response = _build_error_response(str(exc), str(request_id))

        print(response.to_json(), flush=True)


def main() -> None:
    """Entry point for ``python -m mcp.schedule_server``."""

    serve()


if __name__ == "__main__":  # pragma: no cover - module execution guard
    main()
