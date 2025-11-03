from __future__ import annotations

import sys

from backend.domain.schedule_change.entities import ScheduleChangeRequest
from backend.infrastructure.schedule_change.mcp_gateway import MCPScheduleApiGateway


def test_mcp_gateway_success() -> None:
    gateway = MCPScheduleApiGateway(cmd=[sys.executable, "-m", "mcp.schedule_server"])
    try:
        request = ScheduleChangeRequest(
            entry_id="0001",
            prompt="エントリID 0001 の日程変更をお願いします。2024年07月21日15:30に変更希望。理由: 社内調整のため。",
            requester="テストユーザー",
            reason="社内調整のため",
        )
        response = gateway(request)
        assert response.status == "pending"
        assert "現在登録されている日程" in response.message
        assert "理由: 社内調整のため" in response.message
    finally:
        gateway.close()


def test_mcp_gateway_returns_error_when_process_fails() -> None:
    gateway = MCPScheduleApiGateway(cmd=[sys.executable, "-c", "import sys; sys.exit(1)"])
    try:
        request = ScheduleChangeRequest(entry_id="0001", prompt="テスト", requester=None, reason=None)
        response = gateway(request)
        assert response.status == "error"
        assert response.message.startswith("MCP error:")
    finally:
        gateway.close()
