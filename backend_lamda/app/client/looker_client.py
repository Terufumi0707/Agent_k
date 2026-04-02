from __future__ import annotations

from typing import Any

import httpx


class LookerClient:
    def __init__(self, base_url: str, api_key: str, timeout_seconds: float, use_stub: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.use_stub = use_stub

    async def fetch_company_insights(self, company_name: str, theme: str) -> dict[str, Any]:
        if self.use_stub:
            return {
                "company": company_name,
                "theme": theme,
                "kpi": {"arr_growth": 0.18, "churn": 0.06, "nps": 42},
                "signals": ["導入部門の増加", "契約更新時の要件高度化"],
                "source": "stub",
            }

        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"company": company_name, "theme": theme}
        url = f"{self.base_url}/insights"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
