"""LangGraph を用いて日程変更ワークフローを実装したモジュール。"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, Optional, TypedDict, cast

from mock_api.schedule_change_data import get_schedule_scenario

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
    """ノード間で共有する実行状態を保持する辞書型。"""

    prompt: str
    classification: Literal["schedule_change", "other"]
    entry_id: str
    api_result: Optional[str]
    api_status: Optional[str]


@dataclass(frozen=True)
class WorkflowResult:
    """LangGraph ワークフローを実行した際の最終結果。"""

    message: str
    path: list[str]
    classification: Literal["schedule_change", "other"]


@dataclass(frozen=True)
class SchedulePreview:
    """エントリIDに紐づく現在の登録情報を表現する値オブジェクト。"""

    entry_id: str
    message: str
    found: bool


#
# 注意:
#   `\b` は Unicode 対応正規表現では ASCII 数字と日本語の境界を認識できない。
#   そのため「1111日程変更したい」のように 4 桁の数字が含まれていても、
#   単語境界を基準とするとエントリ ID を検出できなかった。
#   そこで数字の前後に別の数字が現れない 4 桁連続のパターンを検出することで、
#   厳密に 4 桁のみを拾いつつ、空白がない日本語文にも対応している。
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
    """プロンプト内に 4 桁のエントリ ID が含まれている場合 True を返す。"""

    return _extract_entry_id(prompt) is not None


def _extract_entry_id(prompt: str) -> Optional[str]:
    """プロンプトから最初に一致した 4 桁のエントリ ID を抽出して返す。"""

    match = ENTRY_ID_PATTERN.search(prompt)
    if match:
        return match.group(1)
    return None


def extract_schedule_entry_id(prompt: str) -> Optional[str]:
    """外部モジュールがエントリID抽出ロジックを再利用できるよう公開する。"""

    return _extract_entry_id(prompt)


def build_schedule_preview(entry_id: str) -> SchedulePreview:
    """エントリIDに紐づく現在の登録情報を取得してメッセージ化する。"""

    scenario = get_schedule_scenario(entry_id)

    if scenario is None:
        message = f"エントリID {entry_id} に関する日程情報を確認できませんでした。"
        return SchedulePreview(entry_id=entry_id, message=message, found=False)

    formatted = scenario.registered_slot.strftime("%Y年%m月%d日 %H:%M")
    message = (
        "現在登録されている日程: "
        f"{scenario.location}での{scenario.sport}を"
        f"{formatted}に実施予定です。"
    )
    return SchedulePreview(entry_id=entry_id, message=message, found=True)


def _contains_schedule_change_request(prompt: str) -> bool:
    """入力文が日程変更を明示的に依頼している場合に True を返す。"""

    if any(keyword in prompt for keyword in SCHEDULE_CHANGE_KEYWORDS_JA):
        return True

    lowered = prompt.casefold()
    return any(keyword in lowered for keyword in SCHEDULE_CHANGE_KEYWORDS_EN)


def _classify_intent_factory(prompts: ScheduleChangePrompts):
    """分類ノードを生成するためのファクトリー関数。"""

    def classify_intent(
        state: WorkflowState, config: WorkflowConfig | None = None
    ) -> WorkflowState:
        """ユーザー入力が日程変更かどうかを判定して状態を返す。"""

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
    """日程変更 API を呼び出すノードを生成するファクトリー。"""

    def call_schedule_api(
        state: WorkflowState, config: WorkflowConfig | None = None
    ) -> WorkflowState:
        """ゲートウェイを利用して日程変更 API を呼び出し結果を状態に格納する。"""

        if config is None:
            config = WorkflowConfig()

        entry_id = state.get("entry_id")

        if entry_id is None:
            raise ValueError("日程変更 API を呼び出すには entry_id が必要です")

        payload = ScheduleChangeRequest(
            entry_id=entry_id,
            prompt=state["prompt"],
            requester=config.requester_name,
            reason=config.reason,
        )
        response = gateway(payload)
        return {"api_result": response.message, "api_status": response.status}

    return call_schedule_api


def should_call_schedule_api(state: WorkflowState) -> bool:
    """分類結果に応じて API 呼び出しが必要かを判定する。"""

    return state.get("classification") == "schedule_change"


def build_schedule_change_app(
    prompts: ScheduleChangePrompts, gateway: ScheduleApiGateway
):
    """LangGraph アプリケーションを構築して状態遷移を定義する。"""

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

        base_message = "日程変更のリクエストであると判断しました。"

        if api_message:
            message = f"{base_message}\n{api_message}"
        elif api_status == "iw":
            message = f"{base_message}\nまだ実装中です。"
        else:
            message = f"{base_message}\nAPI 呼び出しに成功しました。"

        path.append("call_schedule_api")
    else:
        message = "今回は日程変更のリクエストではないと判断しました。"

    return WorkflowResult(message=message, path=path, classification=classification)


__all__ = [
    "build_schedule_change_app",
    "build_schedule_preview",
    "run_schedule_change_workflow",
    "classify_schedule_change_prompt",
    "extract_schedule_entry_id",
    "SchedulePreview",
    "WorkflowState",
    "WorkflowResult",
]
