from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from src.domain.models import InputType, Job, JobStatus
from src.repositories.in_memory_store import InMemoryStore
from src.services.skills import (
    MinutesDraftSkill,
    MinutesExportWordSkill,
    MinutesReviewSkill,
    MinutesTranscribeSkill,
)
from src.services.workflow_loader import WorkflowLoader


class WorkflowOrchestrator:
    def __init__(
        self,
        store: InMemoryStore,
        loader: WorkflowLoader,
        transcribe_skill: MinutesTranscribeSkill,
        draft_skill: MinutesDraftSkill,
        review_skill: MinutesReviewSkill,
        export_skill: MinutesExportWordSkill,
        artifacts_dir: Path,
    ) -> None:
        self.store = store
        self.loader = loader
        self.transcribe_skill = transcribe_skill
        self.draft_skill = draft_skill
        self.review_skill = review_skill
        self.export_skill = export_skill
        self.artifacts_dir = artifacts_dir

    def start(self, input_type: InputType, transcript: str | None, audio_path: str | None) -> Job:
        workflow = self.loader.load_workflow()
        company_format = self.loader.load_company_format()
        context: dict = {
            "input_type": input_type.value,
            "transcript": (transcript or "").strip(),
            "audio_path": audio_path,
            "company_format": company_format,
            "candidate_count": workflow.get("candidate_count", 3),
        }

        for step in workflow["steps"]:
            if step["id"] == "transcribe" and input_type != InputType.AUDIO:
                continue
            if step["id"] == "transcript_input" and input_type != InputType.TRANSCRIPT:
                continue
            if step["id"] == "transcribe":
                context.update(self.transcribe_skill.run(context))
            elif step["id"] == "draft":
                context.update(self.draft_skill.run(context))
            elif step["id"] == "review":
                break

        now = datetime.utcnow()
        job = Job(
            id=str(uuid.uuid4()),
            input_type=input_type,
            status=JobStatus.WAITING_FOR_REVIEW,
            created_at=now,
            updated_at=now,
            transcript=context["transcript"],
            candidates=context["candidates"],
        )
        return self.store.save(job)

    def review(self, job_id: str, selected_index: int, instruction: str | None) -> Job:
        job = self.store.get(job_id)
        if not job:
            raise ValueError("job not found")
        result = self.review_skill.run(
            {
                "candidates": job.candidates,
                "selected_index": selected_index,
                "instruction": instruction,
            }
        )
        job.updated_at = datetime.utcnow()
        if not result["approved"]:
            job.review_comments.append(instruction or "")
            job.candidates.append(result["revised_candidate"])
            return self.store.save(job)

        job.selected_candidate = result["final_minutes"]
        export = self.export_skill.run(
            {
                "job_id": job.id,
                "final_minutes": job.selected_candidate,
                "output_dir": str(self.artifacts_dir),
            }
        )
        job.artifact_path = export["artifact_path"]
        job.status = JobStatus.COMPLETED
        return self.store.save(job)

    def get(self, job_id: str) -> Job | None:
        return self.store.get(job_id)
