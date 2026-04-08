from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from src.config import direct_settings


class LlmClient:
    """Gemini API を呼び出す薄いクライアント。"""

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY") or direct_settings.GEMINI_API_KEY
        self.model = os.getenv("GEMINI_MODEL", direct_settings.GEMINI_MODEL)
        self.timeout = float(os.getenv("GEMINI_TIMEOUT_SECONDS", direct_settings.GEMINI_TIMEOUT_SECONDS))

    def generate_json(self, prompt: str) -> dict[str, Any] | None:
        if not prompt.strip():
            print("[LlmClient] skipped generate_json: prompt is empty")
            return None
        if not self.api_key:
            print("[LlmClient] skipped generate_json: GEMINI_API_KEY is not set")
            return None

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
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
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"[LlmClient] request failed: {exc}")
            return None
        print(f"[LlmClient] raw response: {json.dumps(body, ensure_ascii=False)}")

        text = self._extract_text(body)
        if not text:
            print("[LlmClient] extracted text is empty")
            return None
        print(f"[LlmClient] extracted text: {text}")

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"[LlmClient] failed to parse extracted text as JSON: {exc}")
            return None
        print(f"[LlmClient] parsed json: {json.dumps(parsed, ensure_ascii=False)}")

        return parsed if isinstance(parsed, dict) else None

    def _extract_text(self, response: dict[str, Any]) -> str:
        candidates = response.get("candidates", [])
        if not candidates:
            return ""

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            return ""

        return str(parts[0].get("text", "")).strip()
