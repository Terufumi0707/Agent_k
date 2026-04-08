from __future__ import annotations

from typing import Any


class MinutesReviewSkill:
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
            # 差し戻し時は元候補をコピーし、レビュー内容を追記した改訂版を返す。
            revised = dict(base)
            revised["レビュー反映"] = instruction
            revised = self._apply_revision_intents(
                revised_candidate=revised,
                candidates=candidates,
                selected_index=selected_index,
                transcript=str(payload.get("transcript") or ""),
                review_comments=payload.get("review_comments") or [],
                instruction=instruction,
            )
            print("[MinutesReviewSkill.run] returning revise result", flush=True)
            return {"approved": False, "revised_candidate": revised}
        if action == "approve":
            print("[MinutesReviewSkill.run] returning approve result", flush=True)
            return {"approved": True, "final_minutes": base}
        raise ValueError(f"unsupported review action: {action}")

    def _apply_revision_intents(
        self,
        revised_candidate: dict[str, Any],
        candidates: list[dict[str, Any]],
        selected_index: int,
        transcript: str,
        review_comments: list[Any],
        instruction: str,
    ) -> dict[str, Any]:
        sections = self._to_sections(revised_candidate)
        normalized = instruction.lower()

        if self._wants_reference_past_minutes(normalized):
            sections["参照した過去議事メモ"] = self._build_past_minutes_references(
                candidates=candidates, selected_index=selected_index
            )

        if self._wants_structured_conversation_log(normalized):
            sections["構造化会話ログ"] = self._build_structured_conversation_log(transcript)

        if review_comments:
            sections["レビュー履歴"] = [str(comment).strip() for comment in review_comments if str(comment).strip()]

        revised_candidate["sections"] = sections
        return revised_candidate

    def _to_sections(self, candidate: dict[str, Any]) -> dict[str, Any]:
        explicit_sections = candidate.get("sections")
        if isinstance(explicit_sections, dict):
            return dict(explicit_sections)
        return {k: v for k, v in candidate.items() if k not in {"raw_content", "sections"}}

    def _wants_reference_past_minutes(self, instruction: str) -> bool:
        return "参照" in instruction and ("過去" in instruction or "以前" in instruction)

    def _wants_structured_conversation_log(self, instruction: str) -> bool:
        return "会話ログ" in instruction and ("構造化" in instruction or "残し" in instruction)

    def _build_past_minutes_references(
        self, candidates: list[dict[str, Any]], selected_index: int
    ) -> list[dict[str, Any]]:
        references: list[dict[str, Any]] = []
        for index, candidate in enumerate(candidates):
            if index == selected_index:
                continue
            sections = self._to_sections(candidate)
            references.append(
                {
                    "candidate_index": index,
                    "summary_keys": list(sections.keys()),
                }
            )
        return references

    def _build_structured_conversation_log(self, transcript: str) -> list[dict[str, str]]:
        logs: list[dict[str, str]] = []
        for line in transcript.splitlines():
            normalized = line.strip()
            if not normalized:
                continue
            if "：" in normalized:
                speaker, utterance = normalized.split("：", 1)
            elif ":" in normalized:
                speaker, utterance = normalized.split(":", 1)
            else:
                speaker, utterance = "unknown", normalized
            logs.append({"speaker": speaker.strip() or "unknown", "utterance": utterance.strip()})
        return logs
