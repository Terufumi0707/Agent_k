"""インフラ層で利用する型定義。"""
from __future__ import annotations

from typing import Protocol

from ...domain.schedule_change.entities import (
    ScheduleChangeRequest,
    ScheduleChangeResponse,
)


class ScheduleApiGateway(Protocol):
    """日程変更 API への依存を抽象化するゲートウェイ。"""

    def __call__(self, payload: ScheduleChangeRequest) -> ScheduleChangeResponse:
        """日程変更 API を呼び出す。"""
        ...
