from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from src.api.schemas.request.job_requests import ReviewRequest, StartJobRequest
from src.api.schemas.response.job_responses import JobResponse
from src.config.container import Container

router = APIRouter(prefix="/minutes", tags=["minutes"])
container = Container()
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".mp4"}


@router.post("/uploads/audio")
async def upload_audio(request: Request) -> dict[str, str]:
    form = await request.form()
    file = form.get("file")
    if file is None or not hasattr(file, "filename"):
        raise HTTPException(status_code=400, detail="file is required")

    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="unsupported audio format. only .mp3 and .mp4 are supported")

    artifacts_dir = container.orchestrator.artifacts_dir
    uploads_dir = artifacts_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    saved_path = uploads_dir / f"{uuid4().hex}{suffix}"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    saved_path.write_bytes(content)
    return {"audio_path": str(saved_path), "filename": filename}


@router.post("/jobs", response_model=JobResponse)
def start_job(req: StartJobRequest) -> JobResponse:
    try:
        job = container.orchestrator.start(
            input_type=req.input_type,
            transcript=req.transcript,
            audio_path=req.audio_path,
        )
        return JobResponse.from_domain(job)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
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
