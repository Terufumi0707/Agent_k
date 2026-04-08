from fastapi import APIRouter, HTTPException

from src.api.schemas.request.job_requests import ReviewRequest, StartJobRequest
from src.api.schemas.response.job_responses import JobResponse
from src.config.container import Container

router = APIRouter(prefix="/minutes", tags=["minutes"])
container = Container()


@router.post("/jobs", response_model=JobResponse)
def start_job(req: StartJobRequest) -> JobResponse:
    try:
        job = container.orchestrator.start(
            input_type=req.input_type,
            transcript=req.transcript,
            audio_path=req.audio_path,
        )
        return JobResponse.from_domain(job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/review", response_model=JobResponse)
def review_job(job_id: str, req: ReviewRequest) -> JobResponse:
    try:
        if req.action.value == "revise" and not (req.instruction or "").strip():
            raise ValueError("instruction is required when action is revise")
        job = container.orchestrator.review(job_id, req.selected_index, req.action, req.instruction)
        return JobResponse.from_domain(job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = container.orchestrator.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResponse.from_domain(job)
