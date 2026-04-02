from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ProposalResult(BaseModel):
    looker_data: dict[str, Any]
    gemini_summary: dict[str, Any]
    gas_result: dict[str, Any]
