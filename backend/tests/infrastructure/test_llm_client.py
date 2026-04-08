from __future__ import annotations

import json
from urllib import error, request

from src.infrastructure.llm.llm_client import LlmClient


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_generate_text_retries_other_models_when_404(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    monkeypatch.setenv("GEMINI_MODEL", "missing-model")
    monkeypatch.setenv("GEMINI_MODEL_CANDIDATES", "missing-model,working-model")

    call_count = {"value": 0}

    def fake_urlopen(req: request.Request, timeout: float):
        call_count["value"] += 1
        if "missing-model" in req.full_url:
            raise error.HTTPError(req.full_url, 404, "Not Found", hdrs=None, fp=None)
        return _FakeResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "ok"}],
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(request, "urlopen", fake_urlopen)
    client = LlmClient()

    assert client.generate_text("hello") == "ok"
    assert call_count["value"] == 2


def test_generate_text_returns_none_when_all_models_404(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    monkeypatch.setenv("GEMINI_MODEL", "missing-model")
    monkeypatch.setenv("GEMINI_MODEL_CANDIDATES", "missing-model,also-missing")

    def fake_urlopen(req: request.Request, timeout: float):
        raise error.HTTPError(req.full_url, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr(request, "urlopen", fake_urlopen)
    client = LlmClient()

    assert client.generate_text("hello") is None
