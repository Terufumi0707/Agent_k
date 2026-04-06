from __future__ import annotations

from typing import Any


class LlmClient:
    """PoC用の簡易LLMラッパー。APIキー未設定でも動くフォールバックを優先する。"""

    def generate_structured_minutes(
        self,
        transcript: str,
        format_definition: dict[str, Any],
        num_candidates: int = 3,
        feedback: str | None = None,
        base_draft: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not transcript.strip():
            raise ValueError("transcript is empty")

        sections = [s["name"] for s in format_definition.get("sections", [])]
        count = min(max(num_candidates, 2), 3)
        candidates = []
        for idx in range(1, count + 1):
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
            candidates.append(content)
        return candidates
