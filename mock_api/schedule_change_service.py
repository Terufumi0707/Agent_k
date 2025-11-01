"""Implementation of the mock schedule change API."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Optional

from backend.domain.schedule_change.entities import (
    ScheduleChangeRequest,
    ScheduleChangeResponse,
)

from .schedule_change_data import get_schedule_scenario

_DATE_WITH_YEAR_PATTERN = re.compile(
    r"(?P<year>\d{4})[年/](?P<month>\d{1,2})月?(?P<day>\d{1,2})日?\s*"
    r"(?:(?P<hour>\d{1,2})(?:時|:)(?P<minute>\d{1,2}))?"
)
_DATE_WITHOUT_YEAR_PATTERN = re.compile(
    r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日?\s*"
    r"(?:(?P<hour>\d{1,2})(?:時|:)(?P<minute>\d{1,2}))?"
)
_TIME_ONLY_PATTERN = re.compile(r"(?P<hour>\d{1,2})時(?P<minute>\d{1,2})分")
_REASON_PATTERN = re.compile(r"理由[:：]\s*(?P<reason>[^\n。！!]+)")
_REQUESTER_PATTERN = re.compile(
    r"(?P<name>[\w一-龯ぁ-んァ-ン]{2,})\s*さんから"
)


def _format_datetime(value: datetime) -> str:
    """Format datetime values in a human friendly Japanese style."""

    return value.strftime("%Y年%m月%d日 %H:%M")


def _parse_requested_datetime(
    prompt: str, *, fallback: datetime, scenario_reference: Optional[datetime]
) -> datetime:
    """Extract the requested date and time from the prompt if possible."""

    match = _DATE_WITH_YEAR_PATTERN.search(prompt)
    if match:
        year = int(match.group("year"))
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour") or (scenario_reference.hour if scenario_reference else 0))
        minute = int(match.group("minute") or (scenario_reference.minute if scenario_reference else 0))
        return datetime(year, month, day, hour, minute)

    match = _DATE_WITHOUT_YEAR_PATTERN.search(prompt)
    if match and scenario_reference is not None:
        year = scenario_reference.year
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour") or scenario_reference.hour)
        minute = int(match.group("minute") or scenario_reference.minute)
        return datetime(year, month, day, hour, minute)

    match = _TIME_ONLY_PATTERN.search(prompt)
    if match and scenario_reference is not None:
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        return scenario_reference.replace(hour=hour, minute=minute)

    return fallback


def _extract_reason(prompt: str) -> Optional[str]:
    match = _REASON_PATTERN.search(prompt)
    if match:
        return match.group("reason").strip()
    return None


def _extract_requester(prompt: str, fallback: Optional[str]) -> Optional[str]:
    match = _REQUESTER_PATTERN.search(prompt)
    if match:
        return match.group("name")
    return fallback


def handle_schedule_change_request(
    payload: ScheduleChangeRequest,
) -> ScheduleChangeResponse:
    """Generate a deterministic response for the schedule change workflow."""

    scenario = get_schedule_scenario(payload.entry_id)

    if scenario is None:
        message = (
            f"エントリID {payload.entry_id} に関する日程情報が見つかりませんでした。\n"
            "担当チームに確認し、折り返し連絡します。"
        )
        return ScheduleChangeResponse(status="not_found", message=message)

    requested_datetime = _parse_requested_datetime(
        payload.prompt,
        fallback=(
            scenario.alternative_slots[0]
            if scenario.alternative_slots
            else scenario.registered_slot
        ),
        scenario_reference=scenario.registered_slot,
    )

    reason = _extract_reason(payload.prompt) or payload.reason
    requester = _extract_requester(payload.prompt, payload.requester)

    if scenario.is_iw:
        message_lines = [f"エントリID {payload.entry_id} はIW対象です。"]
        message_lines.append(
            "現在登録されている日程: "
            f"{scenario.location}での{scenario.sport}を"
            f"{_format_datetime(scenario.registered_slot)}に実施予定です。"
        )
        message_lines.append(
            "メール内容から"
            f"{_format_datetime(requested_datetime)}頃に変更希望と解釈しました。"
        )

        if reason:
            message_lines.append(f"理由: {reason}")

        if scenario.alternative_slots:
            message_lines.append("変更候補:")
            message_lines.extend(
                f"- {_format_datetime(slot)} {scenario.location}"
                for slot in scenario.alternative_slots
            )
        else:
            message_lines.append("変更候補: 代替案は未登録です。")

        return ScheduleChangeResponse(status="iw", message="\n".join(message_lines))

    requester_label = f"{requester} さん" if requester else "担当者"
    formatted_requested = _format_datetime(requested_datetime)
    message_lines = [
        f"{requester_label}から {formatted_requested} への日程変更希望を受け付けました。",
        "現在登録されている日程: "
        f"{scenario.location}での{scenario.sport}を"
        f"{_format_datetime(scenario.registered_slot)}に実施予定です。",
    ]

    if reason:
        message_lines.append(f"理由: {reason}")

    message_lines.append("通常対応チームに共有し、確定次第ご連絡します。")

    return ScheduleChangeResponse(status="pending", message="\n".join(message_lines))


__all__ = ["handle_schedule_change_request"]

