"""LangGraph を用いた日程変更ワークフロー。"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from ...domain.schedule_change.entities import ScheduleChangeRequest
from ...domain.workflow.config import WorkflowConfig
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
    api_result: Optional[str]


def _classify_intent_factory(prompts: ScheduleChangePrompts):
    """分類ノードを生成するファクトリー。"""

    def classify_intent(
        state: WorkflowState, config: WorkflowConfig | None = None
    ) -> WorkflowState:
        """ユーザー入力が日程変更かどうかを判定する。"""

        prompt = state["prompt"]

        # --- モック LLM 部分 ---------------------------------------------------
        classification: Literal["schedule_change", "other"] = "schedule_change"

        # # 実運用時の LLM 呼び出し例（API キー設定後にコメントアウトを外す）:
        # from langchain_openai import ChatOpenAI
        #
        # llm = ChatOpenAI(model="gpt-4o", temperature=0)
        # response = llm.invoke(
        #     [
        #         ("system", prompts.system),
        #         ("human", prompts.human_template.format(prompt=prompt)),
        #     ]
        # )
        # classification = response.content.strip()
        # ------------------------------------------------------------------

        return {"classification": classification}

    return classify_intent


def _call_schedule_api_factory(gateway: ScheduleApiGateway):
    """日程変更 API を呼び出すノードを生成する。"""

    def call_schedule_api(
        state: WorkflowState, config: WorkflowConfig | None = None
    ) -> WorkflowState:
        """ゲートウェイを利用して日程変更 API をコールする。"""

        if config is None:
            config = WorkflowConfig()

        payload = ScheduleChangeRequest(
            requester=config.requester_name,
            requested_date=config.desired_date or datetime.now(),
            reason=config.reason,
        )
        response = gateway(payload)
        return {"api_result": response.message}

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
_DEFAULT_APP = build_schedule_change_app(
    DEFAULT_SCHEDULE_CHANGE_PROMPTS, _DEFAULT_GATEWAY
)


def run_schedule_change_workflow(
    prompt: str,
    config: WorkflowConfig | None = None,
    *,
    prompts: ScheduleChangePrompts | None = None,
    gateway: ScheduleApiGateway | None = None,
) -> str:
    """LangGraph ワークフローを実行し、結果メッセージを生成する。"""

    selected_prompts = prompts or DEFAULT_SCHEDULE_CHANGE_PROMPTS
    selected_gateway = gateway or _DEFAULT_GATEWAY

    app = (
        _DEFAULT_APP
        if (selected_prompts == DEFAULT_SCHEDULE_CHANGE_PROMPTS)
        and (selected_gateway is _DEFAULT_GATEWAY)
        else build_schedule_change_app(selected_prompts, selected_gateway)
    )

    initial_state: WorkflowState = {"prompt": prompt}
    final_state = app.invoke(initial_state, config=config)

    if final_state.get("classification") == "schedule_change":
        api_message = final_state.get("api_result") or "API 呼び出しに成功しました。"
        return "日程変更のリクエストであると判断しました。\n" + api_message

    return "今回は日程変更のリクエストではないと判断しました。"


__all__ = [
    "build_schedule_change_app",
    "run_schedule_change_workflow",
    "WorkflowState",
]
