from __future__ import annotations

from dataclasses import dataclass

from app.domain.validators import validate_entry
from app.models.conversation_agent import AgentDecision, ConversationAgent
from app.models.domain_entities import Entry
from app.models.entry_service import EntryService


@dataclass
class WorkflowResult:
    status: str
    entry: Entry | None
    questions: list[str]
    validation_errors: list[dict[str, str]]


class EntryWorkflow:
    def __init__(self, agent: ConversationAgent, service: EntryService) -> None:
        self._agent = agent
        self._service = service

    def handle_input(self, payload: str) -> WorkflowResult:
        decision: AgentDecision = self._agent.interpret(payload)
        if decision.entry is None:
            return WorkflowResult(
                status="need_more_info",
                entry=None,
                questions=decision.questions,
                validation_errors=[],
            )

        validation_errors = validate_entry(decision.entry)
        if validation_errors:
            return WorkflowResult(
                status="validation_failed",
                entry=decision.entry,
                questions=decision.questions,
                validation_errors=validation_errors,
            )

        saved_entry = self._service.register_entry(decision.entry)
        return WorkflowResult(
            status="completed",
            entry=saved_entry,
            questions=[],
            validation_errors=[],
        )
