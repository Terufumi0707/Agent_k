"""日程変更 API へのモック実装。"""
from __future__ import annotations

from datetime import datetime

from .scenarios import get_schedule_scenario
from .typing import ScheduleApiGateway
from ...domain.schedule_change.entities import (
    ScheduleChangeRequest,
    ScheduleChangeResponse,
)


def _format_datetime(value: datetime) -> str:
    """Format datetime values in a human friendly Japanese style."""

    return value.strftime("%Y年%m月%d日 %H:%M")


def _is_iw_entry(entry_id: str) -> bool:
    """Return True when the mocked API determines the entry is an IW case."""

    scenario = get_schedule_scenario(entry_id)
    if scenario is not None:
        return scenario.is_iw
    return False


def send_schedule_change_request(payload: ScheduleChangeRequest) -> ScheduleChangeResponse:
    """外部 API の代わりに歓迎メッセージを生成する。"""

    scenario = get_schedule_scenario(payload.entry_id)

    if _is_iw_entry(payload.entry_id):
        message_lines = [f"エントリID {payload.entry_id} はIW対象です。"]

        if scenario is not None:
            message_lines.append(
                "現在登録されている日程: "
                f"{scenario.location}での{scenario.sport}を"
                f"{_format_datetime(scenario.registered_slot)}に実施予定です。"
            )
        else:
            message_lines.append("現在登録されている日程情報はシステムに存在しません。")

        message_lines.append(
            "メール内容から"
            f"{_format_datetime(payload.requested_date)}頃に変更希望と解釈しました。"
        )

        if payload.reason:
            message_lines.append(f"理由: {payload.reason}")

        if scenario is not None and scenario.alternative_slots:
            message_lines.append("変更候補:")
            message_lines.extend(
                f"- {_format_datetime(slot)} {scenario.location}"
                for slot in scenario.alternative_slots
            )
        else:
            message_lines.append("変更候補: 代替案は未登録です。")

        return ScheduleChangeResponse(status="iw", message="\n".join(message_lines))

    requester = payload.requester or "担当者"
    formatted_date = _format_datetime(payload.requested_date)

    message_lines = [
        f"{requester} さんから {formatted_date} への日程変更希望を受け付けました。",
    ]

    if scenario is not None:
        message_lines.append(
            "現在登録されている日程: "
            f"{scenario.location}での{scenario.sport}を"
            f"{_format_datetime(scenario.registered_slot)}に実施予定です。"
        )

    if payload.reason:
        message_lines.append(f"理由: {payload.reason}")

    message_lines.append("通常対応チームに共有し、確定次第ご連絡します。")

    return ScheduleChangeResponse(status="pending", message="\n".join(message_lines))


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
