"""Utilities for calling the Google Gemini models via LangChain."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterable

import google.generativeai as genai
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

__all__ = [
    "GeminiConfigurationError",
    "GeminiInvocationError",
    "classify_with_gemini",
]


class GeminiConfigurationError(RuntimeError):
    """Raised when the Gemini client cannot be configured properly."""


class GeminiInvocationError(RuntimeError):
    """Raised when the Gemini model invocation fails."""


def _require_api_key() -> str:
    """Return the Gemini API key from the environment or raise an error."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiConfigurationError(
            "GEMINI_API_KEY environment variable is not set."
        )
    return api_key


@lru_cache(maxsize=1)
def _build_chat_model() -> ChatGoogleGenerativeAI:
    """Initialise and cache the Gemini chat model client."""

    api_key = _require_api_key()
    genai.configure(api_key=api_key)
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=api_key,
    )


def _normalise_response_content(content: object) -> str:
    """Convert various response payload shapes into a clean string."""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, Iterable):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        if parts:
            return "".join(parts).strip()

    return str(content or "").strip()


def classify_with_gemini(system_prompt: str, human_prompt: str) -> str:
    """Send classification prompts to Gemini and return the raw response text."""

    try:
        chat_model = _build_chat_model()
    except GeminiConfigurationError:
        raise

    try:
        response = chat_model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
        )
    except Exception as exc:  # pragma: no cover - network/SDK failures
        raise GeminiInvocationError("Failed to invoke Gemini model") from exc

    return _normalise_response_content(getattr(response, "content", ""))
