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
        missing_questions = self._build_missing_questions(entry_id, payload)
        if missing_questions:
            questions = questions + [q for q in missing_questions if q not in questions]

        if not entry_id:
            return AgentDecision(entry=None, questions=questions)

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
            return AgentDecision(entry=None, questions=questions)

        return AgentDecision(
            entry=Entry(entry_id=entry_id, constructions=constructions),
            questions=questions,
        )

    @staticmethod
    def _build_missing_questions(entry_id: str | None, payload: Iterable[dict]) -> list[str]:
        missing: list[str] = []
        if not entry_id:
            missing.append("Aナンバーを教えてください。")

        has_work_type = False
        has_work_date = False
        for item in payload:
            has_work_type = has_work_type or bool(item.get("work_type"))
            has_work_date = has_work_date or bool(item.get("work_date"))

        if not has_work_type:
            missing.append("工事種別を教えてください。")
        if not has_work_date:
            missing.append("日程を教えてください。")

        return missing
