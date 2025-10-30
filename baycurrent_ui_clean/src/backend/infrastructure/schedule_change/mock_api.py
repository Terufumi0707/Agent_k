"""日程変更 API へのモック実装。"""
from __future__ import annotations

from .typing import ScheduleApiGateway
from ...domain.schedule_change.entities import (
    ScheduleChangeRequest,
    ScheduleChangeResponse,
)


def send_schedule_change_request(payload: ScheduleChangeRequest) -> ScheduleChangeResponse:
    """外部 API の代わりに歓迎メッセージを生成する。"""

    formatted_date = payload.requested_date.strftime("%Y-%m-%d")
    requester = payload.requester or "担当者"
    reason = f"（理由: {payload.reason}）" if payload.reason else ""

    return ScheduleChangeResponse(
        status="success",
        message=f"{requester} さんの日程を {formatted_date} に変更しました。{reason}".strip(),
    )


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
