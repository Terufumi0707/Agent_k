import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.graph import build_graph, graph_to_state, state_to_graph
from app.models import (
    IntakeNextRequest,
    IntakeResponse,
    IntakeStartRequest,
    IntakeState,
    AutonomousNextRequest,
    AutonomousResponse,
    AutonomousStartRequest,
    WorkParseRequest,
    WorkParseResponse,
)
from app.autonomous_agent import AutonomousAgent
from app.autonomous_session import autonomous_session_store, save_autonomous_session
from app.work_parser import parse_work_request
from app.session import save_session_state, session_store
from app.controllers import agent_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/api")

graph = build_graph()


def run_graph(state: IntakeState, incoming: dict) -> IntakeState:
    graph_state = state_to_graph(state, incoming)
    result_state = graph.invoke(graph_state)
    return graph_to_state(result_state)


@app.post("/intake/start", response_model=IntakeResponse)
def start_intake(request: IntakeStartRequest) -> IntakeResponse:
    session_id = str(uuid.uuid4())
    state = IntakeState(
        session_id=session_id,
        a_number=None,
        entry_id=None,
        work_changes=[],
        fetch_current_order=False,
    )
    incoming = request.model_dump()
    state = run_graph(state, incoming)
    save_session_state(state)
    assistant_message = state.assistant_message or (
        "内容を確認しました。" if state.status == "completed" else "追加の情報を確認させてください。"
    )
    return IntakeResponse(
        session_id=state.session_id,
        status=state.status,
        message=assistant_message,
        missing_fields=state.missing_fields,
        questions=state.questions,
        order_info=state.order_info,
        assistant_message=assistant_message,
    )


@app.post("/intake/next", response_model=IntakeResponse)
def next_intake(request: IntakeNextRequest) -> IntakeResponse:
    state = session_store.get(request.session_id)
    if not state:
        return IntakeResponse(
            session_id=request.session_id,
            status="invalid_request",
            message="セッションが確認できませんでした。状況を教えてもらえますか？",
            missing_fields=[],
            questions=[],
            order_info=None,
            assistant_message="セッションが確認できませんでした。状況を教えてもらえますか？",
        )

    incoming = request.model_dump()
    state = run_graph(state, incoming)
    save_session_state(state)
    assistant_message = state.assistant_message or (
        "内容を確認しました。" if state.status == "completed" else "追加の情報を確認させてください。"
    )
    return IntakeResponse(
        session_id=state.session_id,
        status=state.status,
        message=assistant_message,
        missing_fields=state.missing_fields,
        questions=state.questions,
        order_info=state.order_info,
        assistant_message=assistant_message,
    )


@app.post("/work/parse", response_model=WorkParseResponse)
def parse_work(request: WorkParseRequest) -> WorkParseResponse:
    parsed = parse_work_request(request.message)
    return WorkParseResponse(**parsed)


@app.post("/autonomous/start", response_model=AutonomousResponse)
def start_autonomous(request: AutonomousStartRequest) -> AutonomousResponse:
    session_id = str(uuid.uuid4())
    agent = AutonomousAgent()
    if request.message:
        result = agent.handle_user_input(request.message)
    else:
        question = agent.initial_prompt()
        result = {"status": "need_more_info", "question": question}
    save_autonomous_session(session_id, agent)
    if result["status"] == "completed":
        return AutonomousResponse(
            session_id=session_id,
            status="completed",
            message="内容を確認しました。",
            result=result.get("result"),
        )
    question = result.get("question") or "追加の情報を確認させてください。"
    return AutonomousResponse(
        session_id=session_id,
        status="need_more_info",
        message=question,
        question=question,
    )


@app.post("/autonomous/next", response_model=AutonomousResponse)
def next_autonomous(request: AutonomousNextRequest) -> AutonomousResponse:
    agent = autonomous_session_store.get(request.session_id)
    if not agent:
        return AutonomousResponse(
            session_id=request.session_id,
            status="invalid_request",
            message="セッションが確認できませんでした。状況を教えてもらえますか？",
            question="セッションが確認できませんでした。状況を教えてもらえますか？",
        )
    result = agent.handle_user_input(request.message)
    save_autonomous_session(request.session_id, agent)
    if result["status"] == "completed":
        return AutonomousResponse(
            session_id=request.session_id,
            status="completed",
            message="内容を確認しました。",
            result=result.get("result"),
        )
    question = result.get("question") or "追加の情報を確認させてください。"
    return AutonomousResponse(
        session_id=request.session_id,
        status="need_more_info",
        message=question,
        question=question,
    )
