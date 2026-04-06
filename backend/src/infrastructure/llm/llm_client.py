from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class GeminiConfig:
    api_key: str
    model: str = "gemini-2.5-flash"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        return cls(
            api_key=api_key,
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            base_url=os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
            timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", "60")),
        )


class LlmClient:
    """Gemini client with structured JSON response contract."""

    def __init__(self, config: GeminiConfig | None = None) -> None:
        self.config = config

    def generate_structured_minutes(
        self,
        transcript: str,
        format_definition: dict[str, Any],
        num_candidates: int = 3,
        feedback: str | None = None,
        base_draft: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if len(transcript.strip()) < 20:
            raise ValueError("Transcript is too short to generate meeting minutes.")

        sections = [s["name"] for s in format_definition["sections"]]
        prompt = self._build_prompt(
            transcript=transcript,
            sections=sections,
            num_candidates=max(2, num_candidates),
            feedback=feedback,
            base_draft=base_draft,
        )

        response_text = self._call_gemini(prompt)
        payload = self._extract_json_payload(response_text)

        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or len(candidates) < 2:
            raise ValueError("LLM response must include at least 2 candidates.")

        normalized: list[dict[str, Any]] = []
        for item in candidates:
            content = item.get("content") if isinstance(item, dict) else None
            if not isinstance(content, dict):
                continue
            normalized.append(content)

        if len(normalized) < 2:
            raise ValueError("LLM response candidates are invalid.")

        return normalized

    def _build_prompt(
        self,
        transcript: str,
        sections: list[str],
        num_candidates: int,
        feedback: str | None,
        base_draft: dict[str, Any] | None,
    ) -> str:
        section_instructions = "\n".join(f"- {name}" for name in sections)
        review_block = ""
        if feedback:
            review_block = f"\n修正指示: {feedback}\n"
        if base_draft:
            review_block += f"\n修正元ドラフト(JSON): {json.dumps(base_draft, ensure_ascii=False)}\n"

        # ユーザー指定の固定プロンプトを先頭にそのまま配置
        base_instruction = (
            "あなたは優秀な戦略コンサルタントです。添付したのはとあるクライアントとの会議のスクリプトですが、議事メモを作成してください。\n"
            "フォーマットは下記の通りでお願いします。 \n"
            "◆TODO（敬称略） ・[to-do 1]（[担当者]、[締切日]〆） \n"
            "◆決定事項 ・[決定事項]"
        )

        return (
            f"{base_instruction}\n\n"
            "出力要件:\n"
            f"1) 候補を{num_candidates}件作成する\n"
            "2) 必ずJSONのみを返す（説明文なし）\n"
            "3) JSONスキーマ: {\"candidates\":[{\"content\":{\"<section>\":[\"...\"]}}]}\n"
            "4) 各セクションは配列で返す\n"
            "5) TODOセクションには可能な限り 担当/期限/内容 を含める\n"
            "6) 下記セクションを必ず含める\n"
            f"{section_instructions}\n"
            f"{review_block}\n"
            f"会議スクリプト:\n{transcript}"
        )

    def _call_gemini(self, prompt: str) -> str:
        if self.config is None:
            self.config = GeminiConfig.from_env()
        url = (
            f"{self.config.base_url}/models/{self.config.model}:generateContent?"
            f"{urllib.parse.urlencode({'key': self.config.api_key})}"
        )
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json",
            },
        }

        request = urllib.request.Request(
            url=url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"Gemini API HTTP error: {exc.code} {message}") from exc
        except urllib.error.URLError as exc:
            raise ValueError(f"Gemini API connection error: {exc.reason}") from exc

        parsed = json.loads(raw)
        candidates = parsed.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini API returned no candidates")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            raise ValueError("Gemini API response text is missing")

        return str(parts[0]["text"])

    def _extract_json_payload(self, response_text: str) -> dict[str, Any]:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response_text, flags=re.DOTALL)
            if not match:
                raise ValueError("LLM response is not valid JSON")
            return json.loads(match.group(0))
