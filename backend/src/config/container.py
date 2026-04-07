from __future__ import annotations

from pathlib import Path

from src.infrastructure.llm.llm_client import LlmClient
from src.orchestrators.workflow_orchestrator import WorkflowOrchestrator
from src.repositories.in_memory_store import InMemoryStore
from src.repositories.job_repository import JobRepository
from src.services.skills import (
    MinutesDraftSkill,
    MinutesExportWordSkill,
    MinutesReviewSkill,
    MinutesTranscribeSkill,
)
from src.services.workflow_loader import WorkflowLoader


class Container:
    def __init__(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        loader = WorkflowLoader(
            workflow_path=repo_root / "workflows" / "meeting_minutes_workflow.yaml",
            format_path=repo_root / "workflows" / "company_minutes_format.yaml",
        )
        job_repository: JobRepository = InMemoryStore()
        self.orchestrator = WorkflowOrchestrator(
            store=job_repository,
            loader=loader,
            transcribe_skill=MinutesTranscribeSkill(),
            draft_skill=MinutesDraftSkill(LlmClient()),
            review_skill=MinutesReviewSkill(),
            export_skill=MinutesExportWordSkill(),
            artifacts_dir=repo_root / "artifacts",
        )
