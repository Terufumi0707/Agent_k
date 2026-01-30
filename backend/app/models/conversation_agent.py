from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from app.llm_client import parse_dialogue_decision
from app.llm_prompts import build_dialogue_prompt
from app.models.domain_entities import Construction, Entry
from app.models.domain_value_objects import WorkType


@dataclass
class AgentDecision:
    entry: Entry | None
    questions: list[str]


class ConversationAgent:
    def interpret(self, entry_id: str | None, payload: Iterable[dict]) -> AgentDecision:
        prompt = build_dialogue_prompt({"entry_id": entry_id, "payload": list(payload)})
        dialogue_result = parse_dialogue_decision(prompt)
        questions = dialogue_result.get("questions") or []

        if not entry_id:
            return AgentDecision(entry=None, questions=questions or ["Aナンバーを教えてください。"])

        constructions: list[Construction] = []
        for item in payload:
            work_type = item.get("work_type")
            work_date = item.get("work_date")
            if not work_type or not work_date:
                continue
            constructions.append(
                Construction(
                    work_type=WorkType(str(work_type)),
                    work_date=date.fromisoformat(str(work_date)),
                )
            )

        if not constructions:
            return AgentDecision(entry=None, questions=questions or ["工事種別と日程を教えてください。"])

        return AgentDecision(
            entry=Entry(entry_id=entry_id, constructions=constructions),
            questions=questions,
        )
