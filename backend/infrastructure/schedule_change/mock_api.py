"""日程変更 API へのモック実装。"""
from __future__ import annotations

import random

from .typing import ScheduleApiGateway
from ...domain.schedule_change.entities import (
    ScheduleChangeRequest,
    ScheduleChangeResponse,
)


def _is_iw_entry(entry_id: str) -> bool:
    """Return True when the mocked API determines the entry is an IW case."""

    return random.choice([True, False])


def send_schedule_change_request(payload: ScheduleChangeRequest) -> ScheduleChangeResponse:
    """外部 API の代わりに歓迎メッセージを生成する。"""

    if _is_iw_entry(payload.entry_id):
        return ScheduleChangeResponse(status="iw", message="まだ実装中です。")

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
