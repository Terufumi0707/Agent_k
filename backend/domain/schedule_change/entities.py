"""日程変更に関するドメインエンティティを定義する。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ScheduleChangeRequest:
    """日程変更 API に送信する入力データ。"""

    entry_id: str
    requester: str
    requested_date: datetime
    reason: Optional[str] = None


@dataclass
class ScheduleChangeResponse:
    """日程変更 API から返却されるレスポンスを表現する。"""

    status: str
    message: str
