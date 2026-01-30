from typing import Dict

from app.autonomous_agent import AutonomousAgent


autonomous_session_store: Dict[str, AutonomousAgent] = {}


def save_autonomous_session(session_id: str, agent: AutonomousAgent) -> None:
    autonomous_session_store[session_id] = agent
