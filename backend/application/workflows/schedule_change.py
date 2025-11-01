"""LangGraph を用いた日程変更ワークフロー。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Literal, Optional, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from ...domain.schedule_change.entities import ScheduleChangeRequest
from ...domain.workflow.config import WorkflowConfig
from ...infrastructure.llm import (
    GeminiConfigurationError,
    GeminiInvocationError,
    classify_with_gemini,
)
from ...infrastructure.schedule_change.mock_api import MockScheduleApiGateway
from ...infrastructure.schedule_change.typing import ScheduleApiGateway
from ...prompts.schedule_change import (
    DEFAULT_SCHEDULE_CHANGE_PROMPTS,
    ScheduleChangePrompts,
)


class WorkflowState(TypedDict, total=False):
    """ワークフロー間で共有される状態を管理する型。"""

    prompt: str
    classification: Literal["schedule_change", "other"]
    entry_id: str
    api_result: Optional[str]
    api_status: Optional[str]


@dataclass(frozen=True)
class WorkflowResult:
    """LangGraph ワークフローの実行結果。"""

    message: str
    path: list[str]
    classification: Literal["schedule_change", "other"]


#
# NOTE:
#   `\b` does not recognise a boundary between ASCII digits and Japanese
#   characters because both are treated as "word" characters in the Unicode
#   aware regular expression engine.  As a result, inputs such as
#   "1111日程変更したい" failed to expose the entry id even though the request
#   clearly contains a 4-digit identifier.  Instead of relying on word
#   boundaries we detect a 4-digit sequence that is not surrounded by other
#   digits.  This keeps the strict "exactly four digits" requirement while
#   handling Japanese text without spaces.
ENTRY_ID_PATTERN = re.compile(r"(?<!\d)(\d{4})(?!\d)")
SCHEDULE_CHANGE_KEYWORDS_JA = (
    "日程変更",
    "予定変更",
    "スケジュール変更",
    "リスケジュール",
    "リスケ",
)
SCHEDULE_CHANGE_KEYWORDS_EN = (
    "reschedule",
    "re-schedule",
    "change schedule",
    "schedule change",
)


def _contains_entry_id(prompt: str) -> bool:
    """Return True when the prompt includes a 4 digit entry id."""

    return _extract_entry_id(prompt) is not None


def _extract_entry_id(prompt: str) -> Optional[str]:
    """Extract the first four digit entry id from the prompt if present."""

    match = ENTRY_ID_PATTERN.search(prompt)
    if match:
        return match.group(1)
    return None


def _contains_schedule_change_request(prompt: str) -> bool:
    """Return True when the prompt explicitly asks for a schedule change."""

    if any(keyword in prompt for keyword in SCHEDULE_CHANGE_KEYWORDS_JA):
        return True

    lowered = prompt.casefold()
    return any(keyword in lowered for keyword in SCHEDULE_CHANGE_KEYWORDS_EN)


def _classify_intent_factory(prompts: ScheduleChangePrompts):
    """分類ノードを生成するファクトリー。"""

    def classify_intent(
        state: WorkflowState, config: WorkflowConfig | None = None
    ) -> WorkflowState:
        """ユーザー入力が日程変更かどうかを判定する。"""

        prompt = state["prompt"]

        entry_id = _extract_entry_id(prompt)

        if entry_id is None or not _contains_schedule_change_request(prompt):
            return {"classification": "other"}

        classification: Literal["schedule_change", "other"] = "schedule_change"

        try:
            response = classify_with_gemini(
                prompts.system,
                prompts.human_template.format(prompt=prompt),
            )
        except GeminiConfigurationError:
            # Gemini が利用できない環境ではモック分類を継続する。
            response = ""
        except GeminiInvocationError:
            response = ""

        if response:
            cleaned = response.strip().lower()
            if cleaned in {"schedule_change", "other"}:
                classification = cast(
                    Literal["schedule_change", "other"], cleaned
                )

        result: WorkflowState = {"classification": classification}

        if classification == "schedule_change":
            result["entry_id"] = entry_id

        return result

    return classify_intent


def _call_schedule_api_factory(gateway: ScheduleApiGateway):
    """日程変更 API を呼び出すノードを生成する。"""

    def call_schedule_api(
        state: WorkflowState, config: WorkflowConfig | None = None
    ) -> WorkflowState:
        """ゲートウェイを利用して日程変更 API をコールする。"""

        if config is None:
            config = WorkflowConfig()

        entry_id = state.get("entry_id")

        if entry_id is None:
            raise ValueError("entry_id is required to call the schedule API")

        payload = ScheduleChangeRequest(
            entry_id=entry_id,
            requester=config.requester_name,
            requested_date=config.desired_date or datetime.now(),
            reason=config.reason,
        )
        response = gateway(payload)
        return {"api_result": response.message, "api_status": response.status}

    return call_schedule_api


def should_call_schedule_api(state: WorkflowState) -> bool:
    """分類結果に応じて API 呼び出しが必要かどうかを返す。"""

    return state.get("classification") == "schedule_change"


def build_schedule_change_app(
    prompts: ScheduleChangePrompts, gateway: ScheduleApiGateway
):
    """LangGraph アプリケーションを構築する。"""

    workflow = StateGraph(WorkflowState)
    workflow.add_node("classify_intent", _classify_intent_factory(prompts))
    workflow.add_node("call_schedule_api", _call_schedule_api_factory(gateway))

    workflow.add_edge(START, "classify_intent")
    workflow.add_conditional_edges(
        "classify_intent",
        should_call_schedule_api,
        {True: "call_schedule_api", False: END},
    )
    workflow.add_edge("call_schedule_api", END)

    return workflow.compile()


_DEFAULT_GATEWAY = MockScheduleApiGateway()


def classify_schedule_change_prompt(
    prompt: str,
    *,
    prompts: ScheduleChangePrompts | None = None,
) -> Literal["schedule_change", "other"]:
    """ユーザー入力が日程変更ワークフローに該当するかを判定する。"""

    selected_prompts = prompts or DEFAULT_SCHEDULE_CHANGE_PROMPTS
    classifier = _classify_intent_factory(selected_prompts)
    state: WorkflowState = {"prompt": prompt}
    result = classifier(state)
    return result.get("classification", "other")


def run_schedule_change_workflow(
    prompt: str,
    config: WorkflowConfig | None = None,
    *,
    prompts: ScheduleChangePrompts | None = None,
    gateway: ScheduleApiGateway | None = None,
) -> WorkflowResult:
    """LangGraph ワークフローを実行し、結果メッセージを生成する。"""

    selected_prompts = prompts or DEFAULT_SCHEDULE_CHANGE_PROMPTS
    selected_gateway = gateway or _DEFAULT_GATEWAY

    classifier = _classify_intent_factory(selected_prompts)
    state: WorkflowState = {"prompt": prompt}
    classification_state = classifier(state)
    classification = classification_state.get("classification", "other")
    path = ["classify_intent"]

    if classification == "schedule_change":
        entry_id = classification_state.get("entry_id") or _extract_entry_id(prompt)
        call_schedule_api = _call_schedule_api_factory(selected_gateway)

        if not entry_id:
            api_message = "エントリIDを特定できなかったため処理を中断しました。"
            api_status: Optional[str] = None
        else:
            api_state = call_schedule_api(
                {"prompt": prompt, "entry_id": entry_id},
                config=config,
            )
            api_message = api_state.get("api_result") or "API 呼び出しに成功しました。"
            api_status = api_state.get("api_status")

        if api_status == "iw":
            message = "日程変更のリクエストであると判断しました。\nまだ実装中です。"
        else:
            message = "日程変更のリクエストであると判断しました。\n" + api_message

        path.append("call_schedule_api")
    else:
        message = "今回は日程変更のリクエストではないと判断しました。"

    return WorkflowResult(message=message, path=path, classification=classification)


__all__ = [
    "build_schedule_change_app",
    "run_schedule_change_workflow",
    "classify_schedule_change_prompt",
    "WorkflowState",
    "WorkflowResult",
]
