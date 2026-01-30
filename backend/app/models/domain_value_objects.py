from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkType:
    value: str

    def normalized(self) -> str:
        return self.value.strip().lower()
