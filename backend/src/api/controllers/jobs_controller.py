from fastapi import APIRouter, HTTPException

from src.api.schemas.request.job_requests import ReviewRequest, StartJobRequest
from src.api.schemas.response.job_responses import JobResponse
from src.config.container import Container
from src.domain.models import InputType

router = APIRouter(prefix="/minutes", tags=["minutes"])
container = Container()


@router.post("/jobs", response_model=JobResponse)
def start_job(req: StartJobRequest) -> JobResponse:
    if req.input_type == InputType.AUDIO and not req.audio_path:
        raise HTTPException(status_code=400, detail="audio_path is required")
    if req.input_type == InputType.TRANSCRIPT and not (req.transcript or "").strip():
        raise HTTPException(status_code=400, detail="transcript is required")

    job = container.orchestrator.start(
        input_type=req.input_type,
        transcript=req.transcript,
        audio_path=req.audio_path,
    )
    return JobResponse(**job.__dict__)


@router.post("/jobs/{job_id}/review", response_model=JobResponse)
def review_job(job_id: str, req: ReviewRequest) -> JobResponse:
    try:
        job = container.orchestrator.review(job_id, req.selected_index, req.instruction)
        return JobResponse(**job.__dict__)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = container.orchestrator.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResponse(**job.__dict__)
