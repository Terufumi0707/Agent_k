from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


class LlmClient:
    """Gemini API を呼び出す薄いクライアント。"""

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        raw_candidates = os.getenv(
            "GEMINI_MODEL_CANDIDATES",
            "gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash",
        )
        self.model_candidates = [candidate.strip() for candidate in raw_candidates.split(",") if candidate.strip()]
        if self.model not in self.model_candidates:
            self.model_candidates.insert(0, self.model)
        self.timeout = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "20"))

    def generate_json(self, prompt: str) -> dict[str, Any] | None:
        text = self.generate_text(prompt, response_mime_type="application/json")
        if not text:
            return None

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, dict) else None

    def generate_text(self, prompt: str, response_mime_type: str = "text/plain") -> str | None:
        if not prompt.strip():
            print("[llm] skip request reason=empty_prompt", flush=True)
            return None
        if not self.api_key:
            print("[llm] skip request reason=missing_gemini_api_key", flush=True)
            return None

        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "responseMimeType": response_mime_type,
                "temperature": 0.4,
            },
        }

        for model_name in self.model_candidates:
            endpoint = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_name}:generateContent?key={self.api_key}"
            )
            print(
                f"[llm] request start model={model_name} mime={response_mime_type} timeout={self.timeout}",
                flush=True,
            )
            req = request.Request(
                endpoint,
                method="POST",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload).encode("utf-8"),
            )

            try:
                with request.urlopen(req, timeout=self.timeout) as res:
                    body = json.loads(res.read().decode("utf-8"))
            except error.HTTPError as exc:
                print(f"[llm] request failed model={model_name} status={exc.code}", flush=True)
                if exc.code == 404:
                    continue
                return None
            except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                print(f"[llm] request failed model={model_name} error={exc}", flush=True)
                return None

            text = self._extract_text(body)
            print(
                f"[llm] request done model={model_name} has_text={bool(text)} text_len={len(text)}",
                flush=True,
            )
            return text or None

        print("[llm] request failed reason=no_available_model", flush=True)
        return None

    def _extract_text(self, response: dict[str, Any]) -> str:
        candidates = response.get("candidates", [])
        if not candidates:
            return ""

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            return ""

        return str(parts[0].get("text", "")).strip()
