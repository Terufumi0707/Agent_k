from __future__ import annotations

import json
from typing import Any

from src.infrastructure.llm.llm_client import LlmClient


class MinutesReviewSkill:
    def __init__(self, llm_client: LlmClient | None = None) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        print(
            "[MinutesReviewSkill.run] invoked: "
            f"selected_index={payload.get('selected_index')}, action={payload.get('action')}",
            flush=True,
        )
        # レビュー対象の候補と指示内容を受け取り、承認/差し戻しを判定する。
        candidates = payload["candidates"]
        selected_index = payload["selected_index"]
        instruction = (payload.get("instruction") or "").strip()
        action = (payload.get("action") or "").strip().lower()
        base = candidates[selected_index]
        if not action:
            raise ValueError("action is required")
        if action == "revise":
            if not instruction:
                raise ValueError("instruction is required when action is revise")
            llm_revised = self._revise_with_llm(
                candidates=candidates,
                selected_index=selected_index,
                instruction=instruction,
                transcript=str(payload.get("transcript") or ""),
                review_comments=payload.get("review_comments") or [],
            )
            revised = llm_revised if llm_revised else dict(base)
            revised["レビュー反映"] = instruction
            print("[MinutesReviewSkill.run] returning revise result", flush=True)
            return {"approved": False, "revised_candidate": revised}
        if action == "approve":
            print("[MinutesReviewSkill.run] returning approve result", flush=True)
            return {"approved": True, "final_minutes": base}
        raise ValueError(f"unsupported review action: {action}")

    def _revise_with_llm(
        self,
        candidates: list[dict[str, Any]],
        selected_index: int,
        instruction: str,
        transcript: str,
        review_comments: list[Any],
    ) -> dict[str, Any] | None:
        if not self.llm_client:
            return None

        prompt = self._build_revision_prompt(
            candidates=candidates,
            selected_index=selected_index,
            instruction=instruction,
            transcript=transcript,
            review_comments=review_comments,
        )
        parsed = self.llm_client.generate_json(prompt)
        if not isinstance(parsed, dict):
            return None
        revised = parsed.get("revised_candidate")
        return revised if isinstance(revised, dict) else None

    def _build_revision_prompt(
        self,
        candidates: list[dict[str, Any]],
        selected_index: int,
        instruction: str,
        transcript: str,
        review_comments: list[Any],
    ) -> str:
        selected_candidate = candidates[selected_index]
        history_comments = [str(comment).strip() for comment in review_comments if str(comment).strip()]
        return "\n".join(
            [
                "あなたは議事メモのレビュー反映アシスタントです。",
                "選択された候補をベースに、レビュー指示を反映した改訂版を作成してください。",
                "過去候補・レビュー履歴・会話ログを必要に応じて参照し、指示の意図を最大限反映してください。",
                "返答は必ずJSONのみで返し、次の形式を厳守してください。",
                '{"revised_candidate": {"raw_content": "...", "sections": {"決定事項": ["..."], "ToDo": ["..."]}}}',
                "sections には、必要なら「参照した過去議事メモ」「構造化会話ログ」「レビュー履歴」を含めてください。",
                "",
                f"レビュー指示:\n{instruction}",
                "",
                "選択中の候補:",
                json.dumps(selected_candidate, ensure_ascii=False),
                "",
                "候補一覧:",
                json.dumps(candidates, ensure_ascii=False),
                "",
                "レビュー履歴:",
                json.dumps(history_comments, ensure_ascii=False),
                "",
                "会議の会話ログ:",
                transcript,
            ]
        )
