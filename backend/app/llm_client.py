from __future__ import annotations

import json

import httpx

from app.settings import (
    get_gemini_api_base_url,
    get_gemini_api_key,
    get_gemini_model,
    get_gemini_timeout_seconds,
)


def generate_raw_text(prompt: str) -> str:
    return generate_with_system_and_user(system_prompt="", user_prompt=prompt)


def generate_with_system_and_user(system_prompt: str, user_prompt: str) -> str:
    api_key = get_gemini_api_key()
    if not api_key:
        return ""

    url = f"{get_gemini_api_base_url().rstrip('/')}/models/{get_gemini_model()}:generateContent"
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
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
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError):
        return ""


async def generate_with_system_and_user_async(system_prompt: str, user_prompt: str) -> str:
    api_key = get_gemini_api_key()
    if not api_key:
        return ""

    url = f"{get_gemini_api_base_url().rstrip('/')}/models/{get_gemini_model()}:generateContent"
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "generationConfig": {"temperature": 0},
    }
    try:
        async with httpx.AsyncClient(timeout=get_gemini_timeout_seconds()) as client:
            response = await client.post(url, params={"key": api_key}, json=payload)
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError):
        return ""
