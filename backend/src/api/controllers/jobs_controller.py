from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

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
        print(
            "[jobs_controller.review_job] request received: "
            f"job_id={job_id}, selected_index={req.selected_index}, action={req.action.value}, "
            f"instruction_present={bool((req.instruction or '').strip())}",
            flush=True,
        )
        if req.action.value == "revise" and not (req.instruction or "").strip():
            raise ValueError("instruction is required when action is revise")
        job = container.orchestrator.review(job_id, req.selected_index, req.action, req.instruction)
        print(
            "[jobs_controller.review_job] request completed: "
            f"job_id={job_id}, status={job.status.value}, candidates_count={len(job.candidates)}",
            flush=True,
        )
        return JobResponse.from_domain(job)
    except ValueError as exc:
        print(
            "[jobs_controller.review_job] request rejected: "
            f"job_id={job_id}, error={exc}",
            flush=True,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = container.orchestrator.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResponse.from_domain(job)


@router.get("/jobs/{job_id}/artifact")
def download_job_artifact(job_id: str) -> FileResponse:
    job = container.orchestrator.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if not job.artifact_path:
        raise HTTPException(status_code=404, detail="artifact not found")

    artifact_path = Path(job.artifact_path)
    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(status_code=404, detail="artifact not found")

    return FileResponse(
        path=artifact_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=artifact_path.name,
    )
