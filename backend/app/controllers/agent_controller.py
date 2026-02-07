from __future__ import annotations

import json
import queue
import threading
from collections.abc import Generator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.entry_api_models import EntryRequest, EntryResponse
from app.orchestrator import CreateEntryOrchestrator

router = APIRouter()
_orchestrator = CreateEntryOrchestrator()


@router.post("/create_entry", response_model=EntryResponse)
def create_entry(request: EntryRequest) -> EntryResponse:
    result, session_id = _orchestrator.run(request.prompt, session_id=request.session_id)
    return EntryResponse(result=result, session_id=session_id)


def _format_sse_event(event: str, payload: dict[str, str | None]) -> str:
    # SSE event format example:
    # event: phase
    # data: {"phase":"PHASE1_SESSION_READY","detail":"...","session_id":"..."}
    return f"event: {event}\n" f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/create_entry/stream")
def create_entry_stream(request: EntryRequest) -> StreamingResponse:
    def event_generator() -> Generator[str, None, None]:
        event_queue: queue.Queue[object] = queue.Queue()
        sentinel = object()
        session_id_holder = {"value": request.session_id}
        phase_holder = {"value": None}

        def on_phase(phase: str, detail: str, session_id: str) -> None:
            session_id_holder["value"] = session_id
            phase_holder["value"] = phase
            payload = {"phase": phase, "detail": detail, "session_id": session_id}
            event_queue.put(_format_sse_event("phase", payload))

        def run_orchestrator() -> None:
            try:
                result, session_id = _orchestrator.run_stream(
                    request.prompt,
                    session_id=session_id_holder["value"],
                    on_phase=on_phase,
                )
                session_id_holder["value"] = session_id
                event_queue.put(
                    _format_sse_event(
                        "done",
                        {"session_id": session_id, "message": result},
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive for stream errors
                event_queue.put(
                    _format_sse_event(
                        "error",
                        {
                            "session_id": session_id_holder["value"],
                            "error": str(exc),
                            "phase": phase_holder["value"],
                        },
                    )
                )
            finally:
                event_queue.put(sentinel)

        thread = threading.Thread(target=run_orchestrator, daemon=True)
        thread.start()

        while True:
            item = event_queue.get()
            if item is sentinel:
                break
            yield item

    return StreamingResponse(event_generator(), media_type="text/event-stream")
