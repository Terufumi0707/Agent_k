from fastapi import APIRouter, HTTPException

from src.api.schemas.request.job_requests import ApproveRequest, CreateJobRequest, FeedbackRequest
from src.api.schemas.response.job_responses import ArtifactResponse, CandidateResponse, JobResponse
from src.config.container import Container

router = APIRouter(prefix="/jobs", tags=["jobs"])
container = Container()


@router.post("", response_model=JobResponse)
def create_job(req: CreateJobRequest) -> JobResponse:
    if req.input_type == "audio" and not req.audio_path:
        raise HTTPException(status_code=400, detail={"code": "invalid_request", "message": "audio_path is required for audio input"})
    if req.input_type == "text" and not (req.transcript_text or "").strip():
        raise HTTPException(status_code=400, detail={"code": "invalid_request", "message": "transcript_text is required for text input"})

    try:
        job = container.orchestrator.create_job(
            workflow_name=req.workflow_name,
            input_type=req.input_type,
            transcript_text=req.transcript_text,
            audio_path=req.audio_path,
        )
        return JobResponse(**job.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "bad_request", "message": str(exc)}) from exc


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = container.orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "job not found"})
    return JobResponse(**job.model_dump())


@router.get("/{job_id}/candidates", response_model=list[CandidateResponse])
def get_candidates(job_id: str) -> list[CandidateResponse]:
    return [CandidateResponse(version_no=d.version_no, content=d.content) for d in container.orchestrator.get_candidates(job_id)]


@router.post("/{job_id}/feedback", response_model=JobResponse)
def post_feedback(job_id: str, req: FeedbackRequest) -> JobResponse:
    try:
        job = container.orchestrator.submit_feedback(job_id, req.target_version_no, req.feedback_text)
        return JobResponse(**job.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "bad_request", "message": str(exc)}) from exc


@router.post("/{job_id}/approve", response_model=JobResponse)
def approve(job_id: str, req: ApproveRequest) -> JobResponse:
    try:
        job = container.orchestrator.approve(job_id, req.target_version_no)
        return JobResponse(**job.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "bad_request", "message": str(exc)}) from exc


@router.get("/{job_id}/artifact", response_model=ArtifactResponse)
def get_artifact(job_id: str) -> ArtifactResponse:
    artifact = container.orchestrator.get_artifact(job_id)
    if not artifact:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "artifact not found"})
    return ArtifactResponse(**artifact.model_dump())
