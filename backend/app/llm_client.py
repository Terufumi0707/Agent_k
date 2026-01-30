from __future__ import annotations

import json
import re
from typing import Dict

import httpx

from app.models import WorkChange
from app.settings import (
    get_gemini_api_base_url,
    get_gemini_api_key,
    get_gemini_model,
    get_gemini_timeout_seconds,
)


def parse_message_with_gemini(prompt: str) -> Dict[str, object]:
    api_key = get_gemini_api_key()
    if not api_key:
        return {}

    url = f"{get_gemini_api_base_url().rstrip('/')}/models/{get_gemini_model()}:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {"temperature": 0},
    }
    try:
        response = httpx.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=get_gemini_timeout_seconds(),
        )
        response.raise_for_status()
        content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return normalize_llm_output(content)
    except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError):
        return {}


def normalize_llm_output(content: str) -> Dict[str, object]:
    trimmed = content.strip()
    if trimmed.startswith("```"):
        trimmed = re.sub(r"^```(?:json)?", "", trimmed).strip()
        trimmed = re.sub(r"```$", "", trimmed).strip()
    raw = json.loads(trimmed)
    output: Dict[str, object] = {}
    if isinstance(raw, dict):
        if raw.get("a_number"):
            output["a_number"] = raw.get("a_number")
        if raw.get("entry_id"):
            output["entry_id"] = raw.get("entry_id")
        work_changes = []
        for item in raw.get("work_changes") or []:
            if not isinstance(item, dict):
                continue
            work_changes.append(
                WorkChange(
                    work_type=item.get("work_type"),
                    desired_date=item.get("desired_date"),
                )
            )
        if work_changes:
            output["work_changes"] = work_changes
    return output
