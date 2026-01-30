from __future__ import annotations

from typing import Dict, List, Optional, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from app.llm_client import parse_dialogue_decision
from app.llm_prompts import build_dialogue_prompt
from app.models import IntakeState, OrderInfo, WorkChange
from app.settings import get_http_timeout_seconds, get_system_api_base_url
from app.session import merge_session_state


class IntakeGraphState(TypedDict):
    session_id: str
    a_number: Optional[str]
    entry_id: Optional[str]
    work_changes: List[WorkChange]
    fetch_current_order: bool
    order_info: Optional[OrderInfo]
    missing_fields: List[str]
    questions: List[str]
    status: str
    logs: List[str]
    incoming: Dict
    last_user_message: Optional[str]
    assistant_message: Optional[str]


GraphStep = Dict[str, object]

GRAPH_STEP_SEQUENCE = (
    "merge_inputs_to_state",
    "validate_and_detect_missing",
    "maybe_fetch_order_info",
    "finalize",
)


def build_graph():
    graph = StateGraph(IntakeGraphState)
    step_handlers = {
        "merge_inputs_to_state": merge_inputs_to_state,
        "validate_and_detect_missing": validate_and_detect_missing,
        "maybe_fetch_order_info": maybe_fetch_order_info,
        "finalize": finalize,
    }
    for step in GRAPH_STEP_SEQUENCE:
        graph.add_node(step, step_handlers[step])
    graph.set_entry_point(GRAPH_STEP_SEQUENCE[0])
    for current_step, next_step in zip(GRAPH_STEP_SEQUENCE, GRAPH_STEP_SEQUENCE[1:]):
        graph.add_edge(current_step, next_step)
    graph.add_edge(GRAPH_STEP_SEQUENCE[-1], END)
    return graph.compile()


def state_to_graph(state: IntakeState, incoming: Dict) -> IntakeGraphState:
    return IntakeGraphState(
        session_id=state.session_id,
        a_number=state.a_number,
        entry_id=state.entry_id,
        work_changes=state.work_changes,
        fetch_current_order=state.fetch_current_order,
        order_info=state.order_info,
        missing_fields=state.missing_fields,
        questions=state.questions,
        status=state.status,
        logs=state.logs,
        incoming=incoming,
        last_user_message=state.last_user_message,
        assistant_message=state.assistant_message,
    )


def graph_to_state(graph_state: IntakeGraphState) -> IntakeState:
    return IntakeState(
        session_id=graph_state["session_id"],
        a_number=graph_state.get("a_number"),
        entry_id=graph_state.get("entry_id"),
        work_changes=graph_state.get("work_changes", []),
        fetch_current_order=graph_state.get("fetch_current_order", False),
        order_info=graph_state.get("order_info"),
        missing_fields=graph_state.get("missing_fields", []),
        questions=graph_state.get("questions", []),
        status=graph_state.get("status", "need_more_info"),
        logs=graph_state.get("logs", []),
        last_user_message=graph_state.get("last_user_message"),
        assistant_message=graph_state.get("assistant_message"),
    )


def merge_inputs_to_state(state: IntakeGraphState) -> IntakeGraphState:
    incoming = state.get("incoming", {})
    intake_state = graph_to_state(state)
    intake_state = merge_session_state(intake_state, incoming)
    _append_log(intake_state, "merge_inputs_to_state")
    return state_to_graph(intake_state, {})


def validate_and_detect_missing(state: IntakeGraphState) -> IntakeGraphState:
    intake_state = graph_to_state(state)
    decision = decide_next_action(intake_state)
    intake_state.missing_fields = decision.get("missing_fields", [])
    intake_state.questions = decision.get("questions", [])
    intake_state.status = decision.get("status", "need_more_info")
    intake_state.assistant_message = decision.get("assistant_message")
    _append_log(intake_state, "validate_and_detect_missing")
    return state_to_graph(intake_state, {})


def maybe_fetch_order_info(state: IntakeGraphState) -> IntakeGraphState:
    intake_state = graph_to_state(state)
    if intake_state.fetch_current_order and (intake_state.a_number or intake_state.entry_id):
        try:
            _append_log(intake_state, "fetch_current_order")
            url = _build_order_lookup_url(intake_state)
            response = httpx.get(url, timeout=get_http_timeout_seconds())
            response.raise_for_status()
            intake_state.order_info = OrderInfo(**response.json())
        except httpx.HTTPError as exc:
            _append_log(intake_state, f"fetch_current_order_failed:{exc}")
    else:
        _append_log(intake_state, "skip_fetch_current_order")
    return state_to_graph(intake_state, {})


def finalize(state: IntakeGraphState) -> IntakeGraphState:
    intake_state = graph_to_state(state)
    _append_log(intake_state, "finalize")
    # future: apply_update
    return state_to_graph(intake_state, {})


def format_work_changes(work_changes: List[WorkChange]) -> List[Dict[str, Optional[str]]]:
    return [
        {"work_type": change.work_type, "desired_date": change.desired_date}
        for change in work_changes
    ]


def decide_next_action(state: IntakeState) -> GraphStep:
    payload = {
        "last_user_message": state.last_user_message,
        "a_number": state.a_number,
        "work_changes": format_work_changes(state.work_changes),
        "assistant_message": state.assistant_message,
    }
    prompt = build_dialogue_prompt(payload)
    response = parse_dialogue_decision(prompt)
    return response or fallback_decision(state)


def fallback_decision(state: IntakeState) -> GraphStep:
    return {
        "status": "need_more_info",
        "missing_fields": ["pending"],
        "questions": ["内容を整理するため、もう少し状況を教えてもらえますか？"],
        "assistant_message": "追加の確認が必要です。",
    }


def _append_log(state: IntakeState, message: str) -> None:
    state.logs.append(message)


def _build_order_lookup_url(state: IntakeState) -> str:
    base_url = get_system_api_base_url()
    if state.a_number:
        return f"{base_url}/orders/by-a-number/{state.a_number}"
    return f"{base_url}/orders/by-entry-id/{state.entry_id}"
