from __future__ import annotations

from typing import Any

import httpx


class GasClient:
    def __init__(self, base_url: str, api_key: str, timeout_seconds: float, use_stub: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.use_stub = use_stub

    async def submit_proposal_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.use_stub:
            return {
                "document_id": "stub-proposal-001",
                "document_url": "https://docs.google.com/document/d/stub-proposal-001",
                "status": "created",
                "source": "stub",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/proposal/create"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
