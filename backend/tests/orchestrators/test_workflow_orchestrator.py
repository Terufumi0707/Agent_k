from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from src.domain.models import InputType, ReviewAction
from src.orchestrators.workflow_orchestrator import WorkflowOrchestrator
from src.repositories.in_memory_store import InMemoryStore


class DummyLoader:
    def __init__(self):
        self.workflow = {
            "candidate_count": 2,
            "steps": [
                {"id": "transcribe"},
                {"id": "transcript_input"},
                {"id": "draft"},
                {"id": "review"},
            ],
        }

    def load_workflow(self) -> dict:
        return self.workflow

    def load_company_format(self) -> dict:
        return {"sections": [{"name": "会議概要", "required": True}]}


def _build_orchestrator(tmp_path: Path):
    transcribe = Mock()
    transcribe.run.return_value = {"transcript": "文字起こし結果"}

    draft = Mock()
    draft.run.return_value = {"candidates": [{"会議概要": "案1"}, {"会議概要": "案2"}]}

    review = Mock()
    review.run.return_value = {"approved": True, "final_minutes": {"会議概要": "案1"}}

    export = Mock()
    export.run.return_value = {"artifact_path": str(tmp_path / "artifact.docx")}

    orchestrator = WorkflowOrchestrator(
        store=InMemoryStore(),
        loader=DummyLoader(),
        transcribe_skill=transcribe,
        draft_skill=draft,
        review_skill=review,
        export_skill=export,
        artifacts_dir=tmp_path,
    )
    return orchestrator, transcribe, draft, review, export


def test_transcript_input_skips_transcribe_and_goes_to_draft(tmp_path):
    orchestrator, transcribe, draft, _, _ = _build_orchestrator(tmp_path)

    job = orchestrator.start(InputType.TRANSCRIPT, transcript="入力テキスト", audio_path=None)

    transcribe.run.assert_not_called()
    draft.run.assert_called_once()
    assert job.transcript == "入力テキスト"


def test_audio_input_runs_transcribe_step(tmp_path):
    orchestrator, transcribe, draft, _, _ = _build_orchestrator(tmp_path)

    job = orchestrator.start(InputType.AUDIO, transcript=None, audio_path="/tmp/a.wav")

    transcribe.run.assert_called_once()
    draft.run.assert_called_once()
    assert job.transcript == "文字起こし結果"


def test_dispatch_table_calls_each_step_handler(tmp_path):
    orchestrator, _, _, _, _ = _build_orchestrator(tmp_path)
    orchestrator._handle_transcribe_step = Mock(return_value=True)
    orchestrator._handle_transcript_input_step = Mock(return_value=True)
    orchestrator._handle_draft_step = Mock(side_effect=lambda ctx: ctx.update({"candidates": [{"会議概要": "案"}]}) or True)
    orchestrator._handle_review_step = Mock(return_value=False)
    orchestrator._step_dispatch_table = {
        "transcribe": (orchestrator._is_audio_input, orchestrator._handle_transcribe_step),
        "transcript_input": (
            orchestrator._is_transcript_input,
            orchestrator._handle_transcript_input_step,
        ),
        "draft": (orchestrator._always_run_step, orchestrator._handle_draft_step),
        "review": (orchestrator._always_run_step, orchestrator._handle_review_step),
    }

    orchestrator.start(InputType.AUDIO, transcript=None, audio_path="/tmp/a.wav")

    orchestrator._handle_transcribe_step.assert_called_once()
    orchestrator._handle_transcript_input_step.assert_not_called()
    orchestrator._handle_draft_step.assert_called_once()
    orchestrator._handle_review_step.assert_called_once()


def test_candidates_are_saved_after_draft(tmp_path):
    orchestrator, _, _, _, _ = _build_orchestrator(tmp_path)

    job = orchestrator.start(InputType.TRANSCRIPT, transcript="入力", audio_path=None)

    assert len(job.candidates) == 2
    assert job.candidates[0].sections["会議概要"] == "案1"


def test_review_approve_transitions_to_final_state(tmp_path):
    orchestrator, _, _, review, export = _build_orchestrator(tmp_path)
    job = orchestrator.start(InputType.TRANSCRIPT, transcript="入力", audio_path=None)

    reviewed = orchestrator.review(job.id, 0, ReviewAction.APPROVE, instruction=None)

    review.run.assert_called_once()
    export.run.assert_called_once()
    assert reviewed.status.value == "COMPLETED"
    assert reviewed.selected_candidate is not None


def test_review_revise_goes_back_to_review_flow(tmp_path):
    orchestrator, _, _, review, export = _build_orchestrator(tmp_path)
    review.run.return_value = {"approved": False, "revised_candidate": {"会議概要": "修正案"}}
    job = orchestrator.start(InputType.TRANSCRIPT, transcript="入力", audio_path=None)

    reviewed = orchestrator.review(job.id, 0, ReviewAction.REVISE, instruction="要約を改善")

    export.run.assert_not_called()
    assert review.run.called
    assert reviewed.status.value == "WAITING_FOR_REVIEW"
    assert reviewed.candidates[-1].sections["会議概要"] == "修正案"
