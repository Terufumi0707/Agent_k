from __future__ import annotations

from typing import Any

from app.client.gas_client import GasClient
from app.client.gemini_client import GeminiClient
from app.client.looker_client import LookerClient


class ProposalService:
    def __init__(self, looker_client: LookerClient, gemini_client: GeminiClient, gas_client: GasClient) -> None:
        self.looker_client = looker_client
        self.gemini_client = gemini_client
        self.gas_client = gas_client

    async def fetch_looker_data(self, target_company: str, theme: str) -> dict[str, Any]:
        return await self.looker_client.fetch_company_insights(company_name=target_company, theme=theme)

    async def run_gemini(self, prompt: str) -> dict[str, Any]:
        return await self.gemini_client.generate_summary(prompt=prompt)

    async def send_to_gas(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.gas_client.submit_proposal_payload(payload=payload)
