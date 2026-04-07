from __future__ import annotations

import json
from typing import Any

from src.infrastructure.llm.llm_client import LlmClient


class MinutesDraftSkill:
    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        # 文字起こし結果と社内フォーマットを使って、複数の候補案を生成する。
        transcript = payload["transcript"]
        if not transcript.strip():
            raise ValueError("transcript is empty")

        format_definition = payload["company_format"]
        num_candidates = min(max(payload.get("candidate_count", 3), 2), 3)
        feedback = payload.get("feedback")
        base_draft = payload.get("base_draft")
        required_sections = [
            s["name"] for s in format_definition.get("sections", []) if s.get("required", False)
        ]

        prompt = "\n".join(
            [
                "あなたは会議の議事録作成アシスタントです。",
                "入力された文字起こしを基に、必ずJSONのみを返してください。",
                '返却形式は {"candidates": [<議事録オブジェクト>, ...]} です。',
                f"候補数は必ず {num_candidates} 件にしてください。",
                f"必須セクション: {required_sections}",
                f"format_definition={json.dumps(format_definition, ensure_ascii=False)}",
                f"transcript={transcript}",
                f"feedback={feedback or ''}",
                f"base_draft={json.dumps(base_draft, ensure_ascii=False) if base_draft else '{}'}",
            ]
        )

        parsed = self.llm_client.generate_json(prompt)
        candidates = self._normalize_candidates(
            parsed=parsed,
            format_definition=format_definition,
            num_candidates=num_candidates,
            feedback=feedback,
            base_draft=base_draft,
            transcript=transcript,
        )
        return {"candidates": candidates}

    def _normalize_candidates(
        self,
        parsed: dict[str, Any] | None,
        format_definition: dict[str, Any],
        num_candidates: int,
        feedback: str | None,
        base_draft: dict[str, Any] | None,
        transcript: str,
    ) -> list[dict[str, Any]]:
        sections = [s["name"] for s in format_definition.get("sections", [])]
        generated = parsed.get("candidates", []) if parsed else []

        normalized: list[dict[str, Any]] = []
        if isinstance(generated, list):
            for candidate in generated[:num_candidates]:
                if not isinstance(candidate, dict):
                    continue
                for section in sections:
                    candidate.setdefault(section, "")
                normalized.append(candidate)

        if normalized:
            return normalized

        fallback_candidates = []
        for idx in range(1, num_candidates + 1):
            content = {
                "会議概要": f"候補{idx}: {transcript[:60]}",
                "議題": [f"議題{idx}-1", f"議題{idx}-2"],
                "決定事項": [f"決定事項{idx}"],
                "ToDo": [f"担当A: フォローアップ{idx}"],
            }
            for section in sections:
                content.setdefault(section, f"{section}（候補{idx}）")
            if feedback:
                content["レビュー反映"] = feedback
            if base_draft:
                content["元ドラフト参照"] = "あり"
            fallback_candidates.append(content)

        return fallback_candidates
