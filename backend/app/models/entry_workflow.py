from __future__ import annotations

from dataclasses import dataclass

from app.domain.validators import validate_entry
from app.models.conversation_agent import AgentDecision, ConversationAgent
from app.models.domain_entities import Entry
from app.models.entry_api_models import EntryPayloadItem
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

    def handle_input(
        self, entry_id: str | None, payload: list[EntryPayloadItem]
    ) -> WorkflowResult:
        normalized_entry_id = entry_id.strip() if entry_id else None
        normalized_payload = _normalize_payload(payload)
        decision: AgentDecision = self._agent.interpret(normalized_entry_id, normalized_payload)
        if (
            not normalized_entry_id
            or not _payload_has_value(normalized_payload, "work_type")
            or not _payload_has_value(normalized_payload, "work_date")
        ):
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


def _normalize_payload(payload: list[EntryPayloadItem]) -> list[dict]:
    normalized: list[dict] = []
    for item in payload:
        normalized_item = item.model_dump()
        work_type = normalized_item.get("work_type")
        if work_type is not None:
            normalized_item["work_type"] = str(work_type).strip() or None
        work_date = normalized_item.get("work_date")
        if work_date is not None:
            normalized_item["work_date"] = str(work_date).strip() or None
        normalized.append(normalized_item)
    return normalized


def _payload_has_value(payload: list[dict], key: str) -> bool:
    return any(bool(item.get(key)) for item in payload)
