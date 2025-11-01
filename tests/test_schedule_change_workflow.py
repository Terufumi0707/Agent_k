"""Tests for the schedule change workflow classification logic."""
from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch


def _install_stubs() -> None:
    """Install lightweight stubs for optional third-party dependencies."""

    if "google" not in sys.modules:
        google_module = types.ModuleType("google")
        sys.modules["google"] = google_module
    else:
        google_module = sys.modules["google"]

    generativeai_module = types.ModuleType("google.generativeai")
    generativeai_module.configure = lambda **_: None
    google_module.generativeai = generativeai_module
    sys.modules["google.generativeai"] = generativeai_module

    langchain_core_module = types.ModuleType("langchain_core")
    langchain_core_messages = types.ModuleType("langchain_core.messages")

    class _Message:  # pragma: no cover - simple data holder
        def __init__(self, content: str):
            self.content = content

    langchain_core_messages.HumanMessage = _Message
    langchain_core_messages.SystemMessage = _Message
    langchain_core_module.messages = langchain_core_messages
    sys.modules.setdefault("langchain_core", langchain_core_module)
    sys.modules["langchain_core.messages"] = langchain_core_messages

    langchain_google_genai = types.ModuleType("langchain_google_genai")

    class _DummyChatModel:  # pragma: no cover - not exercised in tests
        def __init__(self, *_, **__):
            pass

        def invoke(self, *_: object, **__: object) -> object:
            raise AssertionError("Chat model should not be invoked in tests")

    langchain_google_genai.ChatGoogleGenerativeAI = _DummyChatModel
    sys.modules["langchain_google_genai"] = langchain_google_genai

    langgraph_module = types.ModuleType("langgraph")
    langgraph_graph_module = types.ModuleType("langgraph.graph")

    class _DummyStateGraph:  # pragma: no cover - not exercised in tests
        def __init__(self, *_, **__):
            pass

        def add_node(self, *_: object, **__: object) -> None:
            pass

        def add_edge(self, *_: object, **__: object) -> None:
            pass

        def add_conditional_edges(self, *_: object, **__: object) -> None:
            pass

        def compile(self) -> object:
            raise AssertionError("StateGraph should not be compiled in tests")

    langgraph_graph_module.StateGraph = _DummyStateGraph
    langgraph_graph_module.END = object()
    langgraph_graph_module.START = object()
    langgraph_module.graph = langgraph_graph_module
    sys.modules.setdefault("langgraph", langgraph_module)
    sys.modules["langgraph.graph"] = langgraph_graph_module


_install_stubs()

from backend.application.workflows.schedule_change import (  # noqa: E402  pylint: disable=C0413
    classify_schedule_change_prompt,
    run_schedule_change_workflow,
)


class ClassifyScheduleChangePromptTests(unittest.TestCase):
    """Validate that the workflow only triggers under the strict conditions."""

    def setUp(self) -> None:
        patcher = patch(
            "backend.application.workflows.schedule_change.classify_with_gemini",
            autospec=True,
        )
        self.addCleanup(patcher.stop)
        self.mock_classifier = patcher.start()
        self.mock_classifier.return_value = "schedule_change"

    def test_prompt_with_entry_id_and_keyword_triggers_workflow(self) -> None:
        prompt = "エントリID 1234 の日程変更をお願いします。"

        result = classify_schedule_change_prompt(prompt)

        self.assertEqual(result, "schedule_change")
        self.mock_classifier.assert_called_once()

    def test_prompt_with_entry_id_without_spacing_triggers_workflow(self) -> None:
        prompt = "1111日程変更したい"

        result = classify_schedule_change_prompt(prompt)

        self.assertEqual(result, "schedule_change")
        self.mock_classifier.assert_called_once()

    def test_prompt_without_entry_id_is_not_schedule_change(self) -> None:
        prompt = "エントリIDが不明ですが日程変更をしたいです。"

        result = classify_schedule_change_prompt(prompt)

        self.assertEqual(result, "other")
        self.mock_classifier.assert_not_called()

    def test_prompt_without_schedule_change_keyword_is_not_schedule_change(self) -> None:
        prompt = "参加者1234です。来週の議事録は確認しました。"

        result = classify_schedule_change_prompt(prompt)

        self.assertEqual(result, "other")
        self.mock_classifier.assert_not_called()

    def test_english_keyword_with_entry_id_triggers_workflow(self) -> None:
        prompt = "Entry 0420 would like to reschedule the meeting."

        result = classify_schedule_change_prompt(prompt)

        self.assertEqual(result, "schedule_change")
        self.mock_classifier.assert_called_once()


class RunScheduleChangeWorkflowTests(unittest.TestCase):
    """Validate the full workflow behaviour with the mock API."""

    def setUp(self) -> None:
        patcher = patch(
            "backend.application.workflows.schedule_change.classify_with_gemini",
            autospec=True,
        )
        self.addCleanup(patcher.stop)
        self.mock_classifier = patcher.start()
        self.mock_classifier.return_value = "schedule_change"

        patcher = patch(
            "backend.infrastructure.schedule_change.mock_api._is_iw_entry",
            autospec=True,
        )
        self.addCleanup(patcher.stop)
        self.mock_iw_checker = patcher.start()

    def test_returns_placeholder_message_when_iw_entry(self) -> None:
        self.mock_iw_checker.return_value = True

        result = run_schedule_change_workflow("エントリID 5678 の日程変更をお願いします。")

        self.assertEqual(result.classification, "schedule_change")
        self.assertIn("まだ実装中です", result.message)
        self.assertIn("call_schedule_api", result.path)

    def test_executes_schedule_change_when_non_iw_entry(self) -> None:
        self.mock_iw_checker.return_value = False

        result = run_schedule_change_workflow("エントリID 9012 の日程変更をお願いします。")

        self.assertEqual(result.classification, "schedule_change")
        self.assertIn("変更しました", result.message)
        self.assertIn("call_schedule_api", result.path)


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    unittest.main()
