from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from src.domain.models import InputType, ReviewAction
from src.main import app
from src.orchestrators.workflow_orchestrator import WorkflowOrchestrator
from src.repositories.in_memory_store import InMemoryStore


class StaticLoader:
    def load_workflow(self) -> dict:
        return {
            "candidate_count": 2,
            "steps": [
                {"id": "transcribe"},
                {"id": "transcript_input"},
                {"id": "draft"},
                {"id": "review"},
            ],
        }

    def load_company_format(self) -> dict:
        return {
            "sections": [
                {"name": "会議概要", "required": True},
                {"name": "決定事項", "required": True},
            ]
        }


class FakeTranscribeSkill:
    def run(self, payload: dict) -> dict:
        return {"transcript": f"transcribed:{payload['audio_path']}"}


class FakeDraftSkill:
    def run(self, payload: dict) -> dict:
        return {
            "candidates": [
                {"会議概要": payload["transcript"], "決定事項": ["A"]},
                {"会議概要": "alt", "決定事項": ["B"]},
            ]
        }


class FakeReviewSkill:
    def run(self, payload: dict) -> dict:
        selected = payload["candidates"][payload["selected_index"]]
        if payload["action"] == ReviewAction.REVISE.value:
            revised = dict(selected)
            revised["レビュー反映"] = payload["instruction"]
            return {"approved": False, "revised_candidate": revised}
        return {"approved": True, "final_minutes": selected}


class FakeExportSkill:
    def run(self, payload: dict) -> dict:
        return {"artifact_path": f"{payload['output_dir']}/{payload['job_id']}.docx"}


@pytest.fixture
def orchestrator(tmp_path: Path) -> WorkflowOrchestrator:
    return WorkflowOrchestrator(
        store=InMemoryStore(),
        loader=StaticLoader(),
        transcribe_skill=FakeTranscribeSkill(),
        draft_skill=FakeDraftSkill(),
        review_skill=FakeReviewSkill(),
        export_skill=FakeExportSkill(),
        artifacts_dir=tmp_path,
    )


@pytest.fixture
def api_client(orchestrator: WorkflowOrchestrator):
    from fastapi.testclient import TestClient
    from src.api.controllers import jobs_controller

    jobs_controller.container.orchestrator = orchestrator
    return TestClient(app)


@pytest.fixture
def started_job(orchestrator: WorkflowOrchestrator):
    return orchestrator.start(input_type=InputType.TRANSCRIPT, transcript="会議ログ", audio_path=None)
