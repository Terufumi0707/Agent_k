"""ワークフロー実行時の設定値をまとめた値オブジェクト。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkflowConfig:
    """LangGraph の実行を細かく調整するための設定情報。"""

    requester_name: str = "営業担当"
    desired_date: Optional[datetime] = None
    reason: Optional[str] = None
