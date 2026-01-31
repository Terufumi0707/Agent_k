from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.llm_client import parse_dialogue_decision
from app.llm_prompts import build_dialogue_prompt
from app.models.domain_entities import Construction, Entry
from app.models.domain_value_objects import WorkType
from app.nlp import parse_message


@dataclass
class AgentDecision:
    entry: Entry | None
    questions: list[str]


class ConversationAgent:
    def interpret(self, payload: str) -> AgentDecision:
        prompt = build_dialogue_prompt({"payload": payload})
        dialogue_result = parse_dialogue_decision(prompt)
        questions = dialogue_result.get("questions") or []
        parsed = parse_message(payload)
        resolved_entry_id = parsed.get("entry_id") or parsed.get("a_number")

        if not resolved_entry_id:
            return AgentDecision(entry=None, questions=questions)

        constructions: list[Construction] = []
        for item in parsed.get("work_changes") or []:
            work_type = getattr(item, "work_type", None)
            work_date = getattr(item, "desired_date", None)
            if not work_type or not work_date:
                continue
            try:
                parsed_date = date.fromisoformat(str(work_date))
            except ValueError:
                continue
            constructions.append(
                Construction(
                    work_type=WorkType(str(work_type)),
                    work_date=parsed_date,
                )
            )

        if not constructions:
            return AgentDecision(entry=None, questions=questions)

        return AgentDecision(
            entry=Entry(entry_id=resolved_entry_id, constructions=constructions),
            questions=questions,
        )
