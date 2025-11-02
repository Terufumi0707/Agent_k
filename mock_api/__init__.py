"""Utilities that emulate external mock APIs for local development."""

from .mock_backend_chat import mock_reply
from .schedule_change_service import handle_schedule_change_request

__all__ = ["handle_schedule_change_request", "mock_reply"]

