"""Deterministic schedule scenarios used by the mock schedule change API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Tuple


@dataclass(frozen=True)
class ScheduleScenario:
    """Represents the registered schedule and alternatives for an entry."""

    entry_id: str
    sport: str
    location: str
    registered_slot: datetime
    alternative_slots: Tuple[datetime, ...]
    is_iw: bool


def _build_scenarios() -> Dict[str, ScheduleScenario]:
    """Generate deterministic scenarios for entry ids 0001-0100."""

    base_start = datetime(2024, 7, 1, 9, 0)
    sports = (
        ("サッカー", "市立競技場"),
        ("バスケットボール", "第2体育館"),
        ("テニス", "屋外テニスコート"),
        ("野球", "河川敷グラウンド"),
        ("水泳", "アクアアリーナ"),
    )

    scenarios: Dict[str, ScheduleScenario] = {}

    for index in range(1, 101):
        entry_id = f"{index:04d}"
        sport, location = sports[(index - 1) % len(sports)]
        cycle = (index - 1) // len(sports)

        # Stagger the registered slots to avoid identical timestamps.
        registered_slot = base_start + timedelta(
            days=cycle * 7 + (index % 5), hours=(index % 3) * 2
        )

        alternative_slots = tuple(
            registered_slot + timedelta(days=7 * offset, hours=1 + offset)
            for offset in range(1, 4)
        )

        is_iw = index % 4 == 0

        scenarios[entry_id] = ScheduleScenario(
            entry_id=entry_id,
            sport=sport,
            location=location,
            registered_slot=registered_slot,
            alternative_slots=alternative_slots,
            is_iw=is_iw,
        )

    return scenarios


@lru_cache
def _scenarios_cache() -> Dict[str, ScheduleScenario]:
    """Return a cached dictionary of schedule scenarios."""

    return _build_scenarios()


def get_schedule_scenario(entry_id: str) -> ScheduleScenario | None:
    """Return the predefined scenario for the given entry id if available."""

    return _scenarios_cache().get(entry_id)


def list_schedule_scenarios() -> Tuple[ScheduleScenario, ...]:
    """Return all configured schedule scenarios."""

    return tuple(_scenarios_cache().values())


__all__ = [
    "ScheduleScenario",
    "get_schedule_scenario",
    "list_schedule_scenarios",
]

