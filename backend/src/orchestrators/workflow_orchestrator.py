from __future__ import annotations

import uuid
from collections.abc import Callable
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
    """議事録作成ワークフローの進行を管理するオーケストレーター。"""

    StepHandler = Callable[[dict], bool]

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
        self._step_handlers: dict[str, WorkflowOrchestrator.StepHandler] = {
            "transcribe": self._handle_transcribe_step,
            "transcript_input": self._handle_transcript_input_step,
            "draft": self._handle_draft_step,
            "review": self._handle_review_step,
        }

    def start(self, input_type: InputType, transcript: str | None, audio_path: str | None) -> Job:
        # ワークフロー定義と社内フォーマットを読み込み、各スキルに渡す共通コンテキストを組み立てる。
        workflow = self.loader.load_workflow()
        company_format = self.loader.load_company_format()
        context: dict = {
            "input_type": input_type.value,
            "transcript": (transcript or "").strip(),
            "audio_path": audio_path,
            "company_format": company_format,
            "candidate_count": workflow.get("candidate_count", 3),
        }

        # 入力種別に応じて実行対象ステップを絞り込みつつ、スキル実行結果を context に統合する。
        for step in workflow["steps"]:
            step_id = step["id"]
            if self._should_skip_step(step_id, input_type):
                continue
            handler = self._step_handlers.get(step_id)
            if handler and not handler(context):
                break

        # 初回作成時点ではレビュー待ち状態で Job を保存する。
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
        # 対象 Job を取得し、存在しない場合は明示的にエラーとする。
        job = self.store.get(job_id)
        if not job:
            raise ValueError("job not found")

        # 選択候補とユーザー指示をレビュー用スキルへ渡す。
        result = self.review_skill.run(
            {
                "candidates": job.candidates,
                "selected_index": selected_index,
                "instruction": instruction,
            }
        )
        job.updated_at = datetime.utcnow()

        # 未承認の場合は修正版候補を追加し、再レビュー可能な状態で保存する。
        if not result["approved"]:
            job.review_comments.append(instruction or "")
            job.candidates.append(result["revised_candidate"])
            return self.store.save(job)

        # 承認済みの場合は最終版を Word 出力し、完了状態へ遷移する。
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
        # 読み取り専用の取得処理はストアへ委譲する。
        return self.store.get(job_id)

    def _should_skip_step(self, step_id: str, input_type: InputType) -> bool:
        if step_id == "transcribe" and input_type != InputType.AUDIO:
            return True
        if step_id == "transcript_input" and input_type != InputType.TRANSCRIPT:
            return True
        return False

    def _handle_transcribe_step(self, context: dict) -> bool:
        context.update(self.transcribe_skill.run(context))
        return True

    def _handle_transcript_input_step(self, context: dict) -> bool:
        return True

    def _handle_draft_step(self, context: dict) -> bool:
        context.update(self.draft_skill.run(context))
        return True

    def _handle_review_step(self, context: dict) -> bool:
        return False
