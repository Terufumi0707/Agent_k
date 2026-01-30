from typing import Dict

from app.models import IntakeState
from app.nlp import parse_message


session_store: Dict[str, IntakeState] = {}


def save_session_state(state: IntakeState) -> None:
    session_store[state.session_id] = state


def merge_session_state(state: IntakeState, incoming: dict) -> IntakeState:
    message = incoming.get("message")
    if message:
        parsed = parse_message(message)
        for key, value in parsed.items():
            if incoming.get(key) is None:
                incoming[key] = value

    if incoming.get("a_number") is not None:
        state.a_number = incoming.get("a_number")
    if incoming.get("entry_id") is not None:
        state.entry_id = incoming.get("entry_id")
    if "fetch_current_order" in incoming and incoming.get("fetch_current_order") is not None:
        state.fetch_current_order = incoming.get("fetch_current_order")
    if incoming.get("work_changes") is not None:
        state.work_changes = incoming.get("work_changes")
    return state
