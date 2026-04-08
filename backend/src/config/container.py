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
from src.services.minutes_service import MinutesService
from src.services.workflow_loader import WorkflowLoader


class Container:
    def __init__(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        loader = WorkflowLoader.from_default_paths()
        job_repository: JobRepository = InMemoryStore()
        llm_client = LlmClient()
        self.minutes_service = MinutesService(llm_client)
        self.orchestrator = WorkflowOrchestrator(
            store=job_repository,
            loader=loader,
            transcribe_skill=MinutesTranscribeSkill(),
            draft_skill=MinutesDraftSkill(llm_client),
            review_skill=MinutesReviewSkill(llm_client),
            export_skill=MinutesExportWordSkill(llm_client),
            artifacts_dir=repo_root / "artifacts",
        )
