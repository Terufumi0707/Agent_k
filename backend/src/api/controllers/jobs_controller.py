from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.api.schemas.request.job_requests import ReviewRequest, StartJobRequest
from src.api.schemas.response.job_responses import JobResponse
from src.config.container import Container
from src.domain.models import InputType

router = APIRouter(prefix="/minutes", tags=["minutes"])
container = Container()
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".mp4"}


async def _save_uploaded_audio(file: UploadFile, artifacts_dir: Path) -> tuple[Path, str]:
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="unsupported audio format. only .mp3 and .mp4 are supported")

    uploads_dir = artifacts_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    saved_path = uploads_dir / f"{uuid4().hex}{suffix}"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    saved_path.write_bytes(content)
    return saved_path, filename


@router.post("/uploads/audio")
async def upload_audio(file: UploadFile = File(...)) -> dict[str, str]:
    saved_path, filename = await _save_uploaded_audio(file, container.orchestrator.artifacts_dir)
    return {"audio_path": str(saved_path), "filename": filename}


@router.post("/jobs/audio", response_model=JobResponse)
async def start_audio_job(file: UploadFile = File(...)) -> JobResponse:
    saved_path, _ = await _save_uploaded_audio(file, container.orchestrator.artifacts_dir)

    request_model = StartJobRequest(
        input_type=InputType.AUDIO,
        transcript=None,
        audio_path=str(saved_path),
    )
    return start_job(request_model)


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
        print(f"[jobs_controller.start_job] request rejected: {exc}", flush=True)
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
