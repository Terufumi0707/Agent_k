from pathlib import Path

from src.agents.runners.workflow_runners import (
    DraftGenerationRunner,
    ExportRunner,
    RevisionRunner,
    WhisperRunner,
)
from src.infrastructure.llm.llm_client import LlmClient
from src.orchestrators.minutes_workflow_orchestrator import MinutesWorkflowOrchestrator
from src.repositories.in_memory_repositories import (
    InMemoryArtifactRepository,
    InMemoryDraftRepository,
    InMemoryFeedbackRepository,
    InMemoryJobRepository,
)
from src.services.export_service import DocxExporter
from src.services.minutes_generation_service import MinutesGenerationService
from src.services.whisper_service import WhisperService
from src.services.workflow_loader_service import WorkflowLoaderService


class Container:
    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        workflow_base = base_dir / "workflows" / "definitions"
        format_base = base_dir / "workflows" / "formats"
        artifacts_dir = base_dir / ".." / "artifacts"

        llm_client = LlmClient()
        minutes_service = MinutesGenerationService(llm_client)

        self.orchestrator = MinutesWorkflowOrchestrator(
            workflow_loader=WorkflowLoaderService(workflow_base),
            whisper_runner=WhisperRunner(WhisperService()),
            draft_runner=DraftGenerationRunner(minutes_service),
            revision_runner=RevisionRunner(minutes_service),
            export_runner=ExportRunner(DocxExporter(), artifacts_dir.resolve()),
            job_repo=InMemoryJobRepository(),
            draft_repo=InMemoryDraftRepository(),
            feedback_repo=InMemoryFeedbackRepository(),
            artifact_repo=InMemoryArtifactRepository(),
            format_base_path=format_base,
        )
