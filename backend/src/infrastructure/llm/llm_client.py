from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


class LlmClient:
    """Gemini優先 + フォールバック対応の簡易LLMラッパー。"""

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.timeout = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "20"))

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

        if self.api_key:
            generated = self._generate_with_gemini(
                transcript=transcript,
                format_definition=format_definition,
                num_candidates=num_candidates,
                feedback=feedback,
                base_draft=base_draft,
            )
            if generated:
                return generated

        return self._fallback_minutes(
            transcript=transcript,
            format_definition=format_definition,
            num_candidates=num_candidates,
            feedback=feedback,
            base_draft=base_draft,
        )

    def _generate_with_gemini(
        self,
        transcript: str,
        format_definition: dict[str, Any],
        num_candidates: int,
        feedback: str | None,
        base_draft: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

        sections = [s["name"] for s in format_definition.get("sections", [])]
        count = min(max(num_candidates, 2), 3)

        system_instruction = (
            "あなたは会議の議事録作成アシスタントです。"
            "入力された文字起こしを基に、必ずJSONのみを返してください。"
            "返却形式は {\"candidates\": [<議事録オブジェクト>, ...]} です。"
            f"候補数は必ず {count} 件にしてください。"
            f"各候補には最低限次のセクションを含めてください: {sections}。"
        )
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": "\n".join(
                                [
                                    system_instruction,
                                    f"format_definition={json.dumps(format_definition, ensure_ascii=False)}",
                                    f"transcript={transcript}",
                                    f"feedback={feedback or ''}",
                                    f"base_draft={json.dumps(base_draft, ensure_ascii=False) if base_draft else '{}'}",
                                ]
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.4,
            },
        }

        req = request.Request(
            endpoint,
            method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode("utf-8"),
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as res:
                body = json.loads(res.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError):
            return []

        text = self._extract_text(body)
        if not text:
            return []

        try:
            parsed = json.loads(text)
            candidates = parsed.get("candidates", [])
        except json.JSONDecodeError:
            return []

        if not isinstance(candidates, list):
            return []

        normalized: list[dict[str, Any]] = []
        for candidate in candidates[:count]:
            if isinstance(candidate, dict):
                for section in sections:
                    candidate.setdefault(section, "")
                normalized.append(candidate)

        return normalized

    def _extract_text(self, response: dict[str, Any]) -> str:
        candidates = response.get("candidates", [])
        if not candidates:
            return ""

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            return ""

        return str(parts[0].get("text", "")).strip()

    def _fallback_minutes(
        self,
        transcript: str,
        format_definition: dict[str, Any],
        num_candidates: int,
        feedback: str | None,
        base_draft: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        sections = [s["name"] for s in format_definition.get("sections", [])]
        count = min(max(num_candidates, 2), 3)
        fallback_candidates = []
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
            fallback_candidates.append(content)

        return fallback_candidates
