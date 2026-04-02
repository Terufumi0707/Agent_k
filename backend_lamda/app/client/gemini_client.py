from __future__ import annotations

import json
from typing import Any

import httpx


class GeminiClient:
    def __init__(self, api_key: str, model: str, timeout_seconds: float, use_stub: bool = True) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.use_stub = use_stub

    async def generate_summary(self, prompt: str) -> dict[str, Any]:
        if self.use_stub:
            return {
                "executive_summary": "既存KPIを踏まえ、初期導入を短期化する提案が有効です。",
                "proposal_outline": ["背景", "課題", "打ち手", "期待効果", "実行計画"],
                "key_messages": ["価値訴求の一貫性", "導入体験の標準化", "早期成果の可視化"],
                "source": "stub",
            }

        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            body = response.json()

        text = body["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
