"""モック API のシナリオデータへアクセスする互換レイヤー。"""

from __future__ import annotations

from typing import Dict

from mock_api.schedule_change_data import (
    ScheduleScenario,
    get_schedule_scenario as _get_schedule_scenario,
    list_schedule_scenarios,
)


def get_schedule_scenario(entry_id: str) -> ScheduleScenario | None:
    """指定したエントリ ID のシナリオが存在すれば返す。"""

    return _get_schedule_scenario(entry_id)


def _build_lookup() -> Dict[str, ScheduleScenario]:
    """後方互換のために辞書形式のビューを生成する。"""

    return {scenario.entry_id: scenario for scenario in list_schedule_scenarios()}


SCHEDULE_SCENARIOS: Dict[str, ScheduleScenario] = _build_lookup()


__all__ = ["ScheduleScenario", "SCHEDULE_SCENARIOS", "get_schedule_scenario"]

