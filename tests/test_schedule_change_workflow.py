"""Tests for the schedule change workflow classification logic."""
from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


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

from backend.infrastructure.schedule_change.scenarios import (  # noqa: E402  pylint: disable=C0413
    SCHEDULE_SCENARIOS,
)
from backend.application.workflows.schedule_change import (  # noqa: E402  pylint: disable=C0413
    build_schedule_preview,
    classify_schedule_change_prompt,
    extract_schedule_entry_id,
    run_schedule_change_workflow,
)
from mock_api.schedule_change_data import (  # noqa: E402  pylint: disable=C0413
    get_schedule_scenario,
    list_schedule_scenarios,
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

        scenarios = list(SCHEDULE_SCENARIOS.values())
        self.iw_entry = next(s.entry_id for s in scenarios if s.is_iw)
        self.non_iw_entry = next(s.entry_id for s in scenarios if not s.is_iw)

    def test_returns_detailed_message_when_iw_entry(self) -> None:
        result = run_schedule_change_workflow(
            f"エントリID {self.iw_entry} の日程変更をお願いします。"
        )

        self.assertEqual(result.classification, "schedule_change")
        self.assertIn("IW対象", result.message)
        self.assertIn("変更候補", result.message)
        self.assertIn("call_schedule_api", result.path)

    def test_returns_acknowledgement_when_non_iw_entry(self) -> None:
        result = run_schedule_change_workflow(
            f"エントリID {self.non_iw_entry} の日程変更をお願いします。"
        )

        self.assertEqual(result.classification, "schedule_change")
        self.assertIn("受け付けました", result.message)
        self.assertIn("現在登録されている日程", result.message)
        self.assertIn("call_schedule_api", result.path)

    def test_requested_datetime_is_parsed_from_prompt(self) -> None:
        prompt = (
            f"エントリID {self.non_iw_entry} の日程変更をお願いします。"
            "2024年07月21日 15:30に変更希望です。理由: 社内調整のため。"
        )

        result = run_schedule_change_workflow(prompt)

        self.assertEqual(result.classification, "schedule_change")
        self.assertIn("2024年07月21日 15:30", result.message)
        self.assertIn("理由: 社内調整のため", result.message)


class SchedulePreviewTests(unittest.TestCase):
    """Ensure helper utilities expose the registered schedule details."""

    def test_build_preview_includes_registered_schedule_details(self) -> None:
        scenario = next(s for s in list_schedule_scenarios() if not s.is_iw)

        preview = build_schedule_preview(scenario.entry_id)

        self.assertTrue(preview.found)
        self.assertIn("現在登録されている日程", preview.message)
        self.assertIn(scenario.location, preview.message)
        self.assertIn(scenario.sport, preview.message)
        self.assertIn(
            scenario.registered_slot.strftime("%Y年%m月%d日 %H:%M"), preview.message
        )

    def test_build_preview_handles_unknown_entry(self) -> None:
        preview = build_schedule_preview("9999")

        self.assertFalse(preview.found)
        self.assertIn("9999", preview.message)

    def test_extract_schedule_entry_id_returns_first_match(self) -> None:
        scenario = get_schedule_scenario("0001")
        assert scenario is not None
        prompt = f"至急エントリID {scenario.entry_id} の日程変更をお願いします。"

        extracted = extract_schedule_entry_id(prompt)

        self.assertEqual(extracted, scenario.entry_id)


class SuggestWorkflowPreviewTests(unittest.TestCase):
    """Validate that the flow suggestion includes the current schedule."""

    def test_schedule_change_suggestion_appends_preview(self) -> None:
        scenario = next(s for s in list_schedule_scenarios() if not s.is_iw)
        prompt = f"エントリID {scenario.entry_id} の日程変更をお願いします。"

        with patch("backend.api.classify_schedule_change_prompt", return_value="schedule_change"):
            from backend.api import SuggestWorkflowRequest, suggest_workflow  # noqa: E402

            response = suggest_workflow(SuggestWorkflowRequest(message=prompt))

        self.assertIn("現在登録されている日程", response.message)
        self.assertIn(scenario.location, response.message)
        self.assertIn(scenario.sport, response.message)

if __name__ == "__main__":  # pragma: no cover - manual execution helper
    unittest.main()

