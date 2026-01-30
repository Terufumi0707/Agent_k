import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.graph import build_graph, graph_to_state, state_to_graph
from app.models import (
    IntakeNextRequest,
    IntakeResponse,
    IntakeStartRequest,
    IntakeState,
    WorkParseRequest,
    WorkParseResponse,
)
from app.work_parser import parse_work_request
from app.session import save_session_state, session_store

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return IntakeResponse(
        session_id=state.session_id,
        status=state.status,
        message="受付完了しました" if state.status == "completed" else "追加情報が必要です",
        missing_fields=state.missing_fields,
        questions=state.questions,
        order_info=state.order_info,
    )


@app.post("/intake/next", response_model=IntakeResponse)
def next_intake(request: IntakeNextRequest) -> IntakeResponse:
    state = session_store.get(request.session_id)
    if not state:
        return IntakeResponse(
            session_id=request.session_id,
            status="invalid_request",
            message="invalid_request",
            missing_fields=[],
            questions=[],
            order_info=None,
        )

    incoming = request.model_dump()
    state = run_graph(state, incoming)
    save_session_state(state)
    return IntakeResponse(
        session_id=state.session_id,
        status=state.status,
        message="受付完了しました" if state.status == "completed" else "追加情報が必要です",
        missing_fields=state.missing_fields,
        questions=state.questions,
        order_info=state.order_info,
    )


@app.post("/work/parse", response_model=WorkParseResponse)
def parse_work(request: WorkParseRequest) -> WorkParseResponse:
    parsed = parse_work_request(request.message)
    return WorkParseResponse(**parsed)
