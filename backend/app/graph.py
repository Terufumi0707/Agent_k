from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, TypedDict

import httpx
from langgraph.graph import END, StateGraph

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


def build_graph():
    graph = StateGraph(IntakeGraphState)
    graph.add_node("merge_inputs_to_state", merge_inputs_to_state)
    graph.add_node("validate_and_detect_missing", validate_and_detect_missing)
    graph.add_node("maybe_fetch_order_info", maybe_fetch_order_info)
    graph.add_node("finalize", finalize)
    graph.set_entry_point("merge_inputs_to_state")
    graph.add_edge("merge_inputs_to_state", "validate_and_detect_missing")
    graph.add_edge("validate_and_detect_missing", "maybe_fetch_order_info")
    graph.add_edge("maybe_fetch_order_info", "finalize")
    graph.add_edge("finalize", END)
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
    )


def merge_inputs_to_state(state: IntakeGraphState) -> IntakeGraphState:
    incoming = state.get("incoming", {})
    intake_state = graph_to_state(state)
    intake_state = merge_session_state(intake_state, incoming)
    intake_state.logs.append("merge_inputs_to_state")
    new_state = state_to_graph(intake_state, {})
    return new_state


def validate_and_detect_missing(state: IntakeGraphState) -> IntakeGraphState:
    intake_state = graph_to_state(state)
    missing_fields: List[str] = []
    questions: List[str] = []

    if not intake_state.a_number and not intake_state.entry_id:
        missing_fields.append("identifier")
        questions.append("A番号またはエントリIDを入力してください。")

    if not intake_state.work_changes:
        missing_fields.append("work_changes")
        questions.append("変更対象の工事を1件以上入力してください。")
    else:
        for index, work_change in enumerate(intake_state.work_changes):
            if not work_change.work_type:
                missing_fields.append(f"work_changes[{index}].work_type")
                questions.append(f"工事{index + 1}の工事種別を入力してください。")
            if not work_change.desired_date:
                missing_fields.append(f"work_changes[{index}].desired_date")
                questions.append(
                    f"工事{index + 1}の変更希望日をYYYY-MM-DD形式で入力してください。"
                )
            elif not is_valid_date(work_change.desired_date):
                missing_fields.append(f"work_changes[{index}].desired_date")
                questions.append(
                    f"工事{index + 1}の変更希望日をYYYY-MM-DD形式で入力してください。"
                )

    intake_state.missing_fields = missing_fields
    intake_state.questions = questions
    if missing_fields:
        intake_state.status = "need_more_info"
    else:
        intake_state.status = "completed"

    intake_state.logs.append("validate_and_detect_missing")
    return state_to_graph(intake_state, {})


def maybe_fetch_order_info(state: IntakeGraphState) -> IntakeGraphState:
    intake_state = graph_to_state(state)
    if intake_state.fetch_current_order and (intake_state.a_number or intake_state.entry_id):
        try:
            intake_state.logs.append("fetch_current_order")
            base_url = get_system_api_base_url()
            if intake_state.a_number:
                url = f"{base_url}/orders/by-a-number/{intake_state.a_number}"
            else:
                url = f"{base_url}/orders/by-entry-id/{intake_state.entry_id}"
            response = httpx.get(url, timeout=get_http_timeout_seconds())
            response.raise_for_status()
            intake_state.order_info = OrderInfo(**response.json())
        except httpx.HTTPError as exc:
            intake_state.logs.append(f"fetch_current_order_failed:{exc}")
    else:
        intake_state.logs.append("skip_fetch_current_order")
    return state_to_graph(intake_state, {})


def finalize(state: IntakeGraphState) -> IntakeGraphState:
    intake_state = graph_to_state(state)
    intake_state.logs.append("finalize")
    # future: apply_update
    return state_to_graph(intake_state, {})


def is_valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False
