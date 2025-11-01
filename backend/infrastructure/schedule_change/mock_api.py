"""日程変更 API へのモック実装。"""
from __future__ import annotations

from .typing import ScheduleApiGateway
from ...domain.schedule_change.entities import (
    ScheduleChangeRequest,
    ScheduleChangeResponse,
)
from mock_api.schedule_change_service import handle_schedule_change_request


def send_schedule_change_request(payload: ScheduleChangeRequest) -> ScheduleChangeResponse:
    """モック API への委譲ラッパー。"""

    return handle_schedule_change_request(payload)


class MockScheduleApiGateway:
    """日程変更 API のモック実装。"""

    def __call__(self, payload: ScheduleChangeRequest) -> ScheduleChangeResponse:
        return send_schedule_change_request(payload)


__all__ = [
    "MockScheduleApiGateway",
    "ScheduleApiGateway",
    "ScheduleChangeRequest",
    "ScheduleChangeResponse",
    "send_schedule_change_request",
]
