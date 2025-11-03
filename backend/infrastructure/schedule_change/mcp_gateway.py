"""Gateway implementation that delegates schedule change requests to an MCP server."""
from __future__ import annotations

import atexit
import json
import logging
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from typing import List, Optional

from ...domain.schedule_change.entities import (
    ScheduleChangeRequest,
    ScheduleChangeResponse,
)
from .typing import ScheduleApiGateway


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _MCPProcessHandles:
    """Holds references to the subprocess IO streams."""

    process: subprocess.Popen[str]


class MCPScheduleApiGateway(ScheduleApiGateway):
    """Schedule API gateway that communicates with an MCP stdio server."""

    def __init__(self, cmd: Optional[List[str]] = None) -> None:
        self._cmd: List[str] = cmd or [sys.executable, "-m", "mcp.schedule_server"]
        self._handles: Optional[_MCPProcessHandles] = None
        self._lock = threading.Lock()
        atexit.register(self.close)

    def _start_process(self) -> _MCPProcessHandles:
        process = subprocess.Popen(
            self._cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        logger.info("mcp_schedule_process_started cmd=%s", self._cmd)
        return _MCPProcessHandles(process=process)

    def _ensure_process(self) -> _MCPProcessHandles:
        if self._handles is not None:
            process = self._handles.process
            if process.poll() is None:
                return self._handles
            logger.warning("mcp_schedule_process_restarting exit_code=%s", process.poll())
            self._terminate_process(process)
            self._handles = None

        try:
            self._handles = self._start_process()
        except OSError as exc:
            logger.error("failed to start MCP process: %s", exc)
            raise

        return self._handles

    def _terminate_process(self, process: subprocess.Popen[str]) -> None:
        try:
            process.terminate()
        except Exception:  # pragma: no cover - best effort shutdown
            return

    def close(self) -> None:
        """Terminate the spawned MCP process if it is still running."""

        if self._handles is None:
            return

        process = self._handles.process
        if process.poll() is None:
            try:
                process.terminate()
            except Exception:  # pragma: no cover - best effort shutdown
                pass
        self._handles = None

    def __call__(self, payload: ScheduleChangeRequest) -> ScheduleChangeResponse:
        with self._lock:
            try:
                handles = self._ensure_process()
            except Exception as exc:
                logger.error("mcp_schedule_process_unavailable error=%s", exc)
                return ScheduleChangeResponse(
                    status="error",
                    message=f"MCP error: {exc}",
                )

            process = handles.process
            if process.stdin is None or process.stdout is None:
                logger.error("mcp_schedule_invalid_streams")
                return ScheduleChangeResponse(status="error", message="MCP error: invalid streams")

            request_id = str(uuid.uuid4())
            message = {
                "method": "tool.call",
                "tool": "schedule.change",
                "args": {
                    "entry_id": payload.entry_id,
                    "prompt": payload.prompt,
                    "requester": payload.requester,
                    "reason": payload.reason,
                },
                "id": request_id,
            }

            logger.info(
                "mcp_schedule_change_call id=%s entry_id=%s", request_id, payload.entry_id
            )

            try:
                process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
                process.stdin.flush()
            except Exception as exc:
                logger.error("mcp_schedule_write_failed id=%s error=%s", request_id, exc)
                self.close()
                return ScheduleChangeResponse(status="error", message=f"MCP error: {exc}")

            try:
                raw_response = process.stdout.readline()
            except Exception as exc:
                logger.error("mcp_schedule_read_failed id=%s error=%s", request_id, exc)
                self.close()
                return ScheduleChangeResponse(status="error", message=f"MCP error: {exc}")

            if not raw_response:
                stderr_output = ""
                if process.stderr is not None:
                    try:
                        stderr_output = process.stderr.read().strip()
                    except Exception:  # pragma: no cover - best effort logging
                        stderr_output = ""
                logger.error(
                    "mcp_schedule_no_response id=%s stderr=%s", request_id, stderr_output
                )
                self.close()
                return ScheduleChangeResponse(
                    status="error",
                    message="MCP error: no response from server",
                )

            try:
                response_payload = json.loads(raw_response)
            except json.JSONDecodeError as exc:
                logger.error(
                    "mcp_schedule_invalid_json id=%s payload=%s", request_id, raw_response
                )
                self.close()
                return ScheduleChangeResponse(status="error", message=f"MCP error: {exc}")

            error_obj = response_payload.get("error")
            if error_obj:
                message_text = error_obj.get("message", "unknown error")
                logger.error(
                    "mcp_schedule_tool_error id=%s message=%s", request_id, message_text
                )
                return ScheduleChangeResponse(
                    status="error",
                    message=f"MCP error: {message_text}",
                )

            result_obj = response_payload.get("result")
            if not isinstance(result_obj, dict):
                logger.error(
                    "mcp_schedule_invalid_result id=%s payload=%s", request_id, response_payload
                )
                return ScheduleChangeResponse(
                    status="error",
                    message="MCP error: invalid result payload",
                )

            status_value = result_obj.get("status")
            message_text = result_obj.get("message")

            if not isinstance(status_value, str) or not isinstance(message_text, str):
                logger.error(
                    "mcp_schedule_result_missing_fields id=%s payload=%s",
                    request_id,
                    result_obj,
                )
                return ScheduleChangeResponse(
                    status="error",
                    message="MCP error: invalid result fields",
                )

            return ScheduleChangeResponse(status=status_value, message=message_text)


__all__ = ["MCPScheduleApiGateway"]
