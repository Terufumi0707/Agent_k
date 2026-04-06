from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.runners.workflow_runners import (
    DraftGenerationRunner,
    ExportRunner,
    RevisionRunner,
    WhisperRunner,
)
from src.domain.entities.models import Artifact, DraftVersion, Feedback, Job, JobStep
from src.domain.enums.feedback_type import FeedbackType
from src.domain.enums.input_type import InputType
from src.domain.enums.job_status import JobStatus
from src.repositories.in_memory_repositories import (
    InMemoryArtifactRepository,
    InMemoryDraftRepository,
    InMemoryFeedbackRepository,
    InMemoryJobRepository,
)
from src.services.workflow_loader_service import WorkflowLoaderService


class MinutesWorkflowOrchestrator:
    def __init__(
        self,
        workflow_loader: WorkflowLoaderService,
        whisper_runner: WhisperRunner,
        draft_runner: DraftGenerationRunner,
        revision_runner: RevisionRunner,
        export_runner: ExportRunner,
        job_repo: InMemoryJobRepository,
        draft_repo: InMemoryDraftRepository,
        feedback_repo: InMemoryFeedbackRepository,
        artifact_repo: InMemoryArtifactRepository,
        format_base_path: Path,
    ) -> None:
        self.workflow_loader = workflow_loader
        self.whisper_runner = whisper_runner
        self.draft_runner = draft_runner
        self.revision_runner = revision_runner
        self.export_runner = export_runner
        self.job_repo = job_repo
        self.draft_repo = draft_repo
        self.feedback_repo = feedback_repo
        self.artifact_repo = artifact_repo
        self.format_base_path = format_base_path

    def create_job(
        self,
        workflow_name: str,
        input_type: InputType,
        transcript_text: str | None,
        audio_path: str | None,
    ) -> Job:
        now = datetime.utcnow()
        job = Job(
            id=str(uuid.uuid4()),
            status=JobStatus.CREATED,
            input_type=input_type,
            workflow_name=workflow_name,
            created_at=now,
            updated_at=now,
        )
        self.job_repo.save_job(job)
        self.job_repo.upsert_context(
            job.id,
            {
                "transcript": transcript_text or "",
                "audio_path": audio_path,
                "selected_candidate_version": None,
                "final_minutes": None,
            },
        )
        self._run_until_review(job.id)
        return self.job_repo.get_job(job.id)

    def _run_until_review(self, job_id: str) -> None:
        job = self._must_get_job(job_id)
        context = self.job_repo.get_context(job_id)
        workflow = self.workflow_loader.load(job.workflow_name)
        format_definition = self.workflow_loader.load_format(workflow["context"]["format_name"], self.format_base_path)
        # Zenn記事のワークフロー設計に合わせ、step id と next で遷移を管理する。
        step_map = {step["id"]: step for step in workflow["steps"]}
        current_step_id = workflow.get("start_at", workflow["steps"][0]["id"])

        while current_step_id:
            step = step_map[current_step_id]
            step_type = step["type"]
            condition = step.get("condition")
            if condition and not self._evaluate_condition(condition, job, context):
                current_step_id = step.get("next")
                continue

            if step_type == "pass_through":
                # テキスト入力時の transcript をコンテキストに転記するだけの軽量ステップ
                context["transcript"] = context.get("transcript") or ""
                self._record_step(job_id, step["name"], job.status, {}, {"transcript_forwarded": True})

            elif step_type == "transcribe":
                self.job_repo.update_status(job_id, JobStatus.TRANSCRIBING)
                result = self.whisper_runner.run({"audio_path": context["audio_path"]})
                context.update(result)
                self.job_repo.update_status(job_id, JobStatus.TRANSCRIBED)
                self._record_step(job_id, step["name"], JobStatus.TRANSCRIBED, {"audio_path": context["audio_path"]}, result)

            elif step_type == "generate_draft":
                self.job_repo.update_status(job_id, JobStatus.DRAFT_GENERATING)
                result = self.draft_runner.run(
                    {
                        "transcript": context["transcript"],
                        "format_definition": format_definition,
                        "num_candidates": step.get("num_candidates", 3),
                    }
                )
                for candidate in result["candidates"]:
                    version = len(self.draft_repo.list_by_job(job_id)) + 1
                    self.draft_repo.add(
                        DraftVersion(
                            job_id=job_id,
                            version_no=version,
                            content=candidate,
                            created_at=datetime.utcnow(),
                        )
                    )
                self.job_repo.update_status(job_id, JobStatus.WAITING_FOR_REVIEW)
                self._record_step(job_id, step["name"], JobStatus.WAITING_FOR_REVIEW, {"transcript": "..."}, {"candidate_count": len(result["candidates"])})

            elif step_type == "human_review":
                self.job_repo.update_status(job_id, JobStatus.WAITING_FOR_REVIEW)
                self._record_step(job_id, step["name"], JobStatus.WAITING_FOR_REVIEW, {}, {"action": "pause_for_human_review"})
                break

            context["format_definition"] = format_definition
            self.job_repo.upsert_context(job_id, context)
            current_step_id = step.get("next")

    def submit_feedback(self, job_id: str, target_version_no: int, feedback_text: str) -> Job:
        self._must_get_job(job_id)
        selected = self.draft_repo.get_version(job_id, target_version_no)
        if not selected:
            raise ValueError("target draft version not found")

        context = self.job_repo.get_context(job_id)
        self.job_repo.update_status(job_id, JobStatus.REVISING)
        self.feedback_repo.add(
            Feedback(
                job_id=job_id,
                target_version_no=target_version_no,
                feedback_type=FeedbackType.REVISION_REQUEST.value,
                feedback_text=feedback_text,
                created_at=datetime.utcnow(),
            )
        )

        result = self.revision_runner.run(
            {
                "transcript": context["transcript"],
                "format_definition": context["format_definition"],
                "base_draft": selected.content,
                "feedback_text": feedback_text,
            }
        )
        next_version = len(self.draft_repo.list_by_job(job_id)) + 1
        self.draft_repo.add(
            DraftVersion(
                job_id=job_id,
                version_no=next_version,
                content=result["revised_candidate"],
                created_at=datetime.utcnow(),
            )
        )

        self.job_repo.update_status(job_id, JobStatus.WAITING_FOR_REVIEW)
        self._record_step(job_id, "revise_draft", JobStatus.WAITING_FOR_REVIEW, {"feedback": feedback_text}, {"new_version_no": next_version})
        return self._must_get_job(job_id)

    def approve(self, job_id: str, target_version_no: int) -> Job:
        self._must_get_job(job_id)
        selected = self.draft_repo.get_version(job_id, target_version_no)
        if not selected:
            raise ValueError("target draft version not found")

        context = self.job_repo.get_context(job_id)
        context["final_minutes"] = selected.content
        self.job_repo.upsert_context(job_id, context)
        self.feedback_repo.add(
            Feedback(
                job_id=job_id,
                target_version_no=target_version_no,
                feedback_type=FeedbackType.APPROVE.value,
                feedback_text="approved",
                created_at=datetime.utcnow(),
            )
        )

        self.job_repo.update_status(job_id, JobStatus.APPROVED)
        self.job_repo.update_status(job_id, JobStatus.EXPORTING)
        export_result = self.export_runner.run({"job_id": job_id, "final_minutes": selected.content})

        self.artifact_repo.add(
            Artifact(
                job_id=job_id,
                artifact_type="minutes_docx",
                file_path=export_result["artifact_path"],
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        )
        self.job_repo.update_status(job_id, JobStatus.COMPLETED)
        self._record_step(job_id, "export_minutes", JobStatus.COMPLETED, {"version": target_version_no}, export_result)
        return self._must_get_job(job_id)

    def get_job(self, job_id: str) -> Job | None:
        return self.job_repo.get_job(job_id)

    def get_candidates(self, job_id: str) -> list[DraftVersion]:
        return self.draft_repo.list_by_job(job_id)

    def get_artifact(self, job_id: str) -> Artifact | None:
        return self.artifact_repo.get_latest(job_id, "minutes_docx")

    def _must_get_job(self, job_id: str) -> Job:
        job = self.job_repo.get_job(job_id)
        if not job:
            raise ValueError("job not found")
        return job

    def _evaluate_condition(self, condition: str, job: Job, context: dict[str, Any]) -> bool:
        if condition == "input_type == 'audio'":
            return job.input_type == InputType.AUDIO
        if condition == "input_type == 'text'":
            return job.input_type == InputType.TEXT
        if condition == "transcript_exists":
            return bool(context.get("transcript", "").strip())
        return True

    def _record_step(
        self,
        job_id: str,
        step_name: str,
        status: JobStatus,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
    ) -> None:
        self.job_repo.add_step(
            JobStep(
                job_id=job_id,
                step_name=step_name,
                status=status,
                input_payload=input_payload,
                output_payload=output_payload,
            )
        )
