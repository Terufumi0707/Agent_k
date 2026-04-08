from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from src.domain.models import (
    InputType,
    Job,
    JobStatus,
    MinuteCandidate,
    ReviewAction,
    minute_candidates_to_dicts,
    to_minute_candidates,
)
from src.repositories.job_repository import JobRepository
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
    StepEligibility = Callable[[InputType], bool]

    def __init__(
        self,
        store: JobRepository,
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
        self._step_dispatch_table: dict[
            str, tuple[WorkflowOrchestrator.StepEligibility, WorkflowOrchestrator.StepHandler]
        ] = {
            "transcribe": (self._is_audio_input, self._handle_transcribe_step),
            "transcript_input": (self._is_transcript_input, self._handle_transcript_input_step),
            "draft": (self._always_run_step, self._handle_draft_step),
            "review": (self._always_run_step, self._handle_review_step),
        }

    def start(self, input_type: InputType, transcript: str | None, audio_path: str | None) -> Job:
        print(
            f"[workflow] start requested input_type={input_type.value} "
            f"transcript_len={len((transcript or '').strip())} audio_path={audio_path}",
            flush=True,
        )
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
            print(f"[workflow] evaluating step={step_id}", flush=True)
            dispatch = self._step_dispatch_table.get(step_id)
            if not dispatch:
                print(f"[workflow] skipping step={step_id} reason=no_dispatch", flush=True)
                continue

            can_run, handler = dispatch
            if not can_run(input_type):
                print(f"[workflow] skipping step={step_id} reason=not_eligible", flush=True)
                continue
            print(f"[workflow] running step={step_id}", flush=True)
            if not handler(context):
                print(f"[workflow] step={step_id} requested stop", flush=True)
                break
            print(f"[workflow] completed step={step_id}", flush=True)

        # 初回作成時点ではレビュー待ち状態で Job を保存する。
        now = datetime.utcnow()
        job = Job(
            id=str(uuid.uuid4()),
            input_type=input_type,
            status=JobStatus.WAITING_FOR_REVIEW,
            created_at=now,
            updated_at=now,
            transcript=context["transcript"],
            candidates=to_minute_candidates(context["candidates"]),
        )
        print(
            f"[workflow] job created id={job.id} status={job.status.value} "
            f"candidates={len(job.candidates)}",
            flush=True,
        )
        return self.store.save(job)

    def review(
        self, job_id: str, selected_index: int, action: ReviewAction, instruction: str | None
    ) -> Job:
        print(
            f"[workflow] review requested job_id={job_id} selected_index={selected_index} "
            f"action={action.value}",
            flush=True,
        )
        # 対象 Job を取得し、存在しない場合は明示的にエラーとする。
        job = self.store.get(job_id)
        if not job:
            print(f"[workflow] review failed job_id={job_id} reason=not_found", flush=True)
            raise ValueError("job not found")
        if selected_index < 0 or selected_index >= len(job.candidates):
            print(
                f"[workflow] review failed job_id={job_id} reason=index_out_of_range "
                f"candidates={len(job.candidates)}",
                flush=True,
            )
            raise ValueError("selected_index is out of range")
        normalized_instruction = (instruction or "").strip()
        if action == ReviewAction.REVISE and not normalized_instruction:
            print(f"[workflow] review failed job_id={job_id} reason=missing_instruction", flush=True)
            raise ValueError("instruction is required when action is revise")

        # 選択候補とユーザー指示をレビュー用スキルへ渡す。
        result = self.review_skill.run(
            {
                "candidates": minute_candidates_to_dicts(job.candidates),
                "selected_index": selected_index,
                "action": action.value,
                "instruction": normalized_instruction or None,
            }
        )
        job.updated_at = datetime.utcnow()

        # 未承認の場合は修正版候補を追加し、再レビュー可能な状態で保存する。
        if action == ReviewAction.REVISE:
            job.review_comments.append(normalized_instruction)
            job.candidates.append(MinuteCandidate.from_dict(result["revised_candidate"]))
            print(
                f"[workflow] review revised job_id={job.id} candidates={len(job.candidates)}",
                flush=True,
            )
            return self.store.save(job)

        # 承認済みの場合は最終版を Word 出力し、完了状態へ遷移する。
        job.selected_candidate = MinuteCandidate.from_dict(result["final_minutes"])
        export = self.export_skill.run(
            {
                "job_id": job.id,
                "final_minutes": job.selected_candidate.to_dict(),
                "output_dir": str(self.artifacts_dir),
            }
        )
        job.artifact_path = export["artifact_path"]
        job.status = JobStatus.COMPLETED
        print(
            f"[workflow] review approved job_id={job.id} status={job.status.value} "
            f"artifact_path={job.artifact_path}",
            flush=True,
        )
        return self.store.save(job)

    def get(self, job_id: str) -> Job | None:
        # 読み取り専用の取得処理はストアへ委譲する。
        return self.store.get(job_id)

    def _always_run_step(self, _: InputType) -> bool:
        return True

    def _is_audio_input(self, input_type: InputType) -> bool:
        return input_type == InputType.AUDIO

    def _is_transcript_input(self, input_type: InputType) -> bool:
        return input_type == InputType.TRANSCRIPT

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
