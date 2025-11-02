"""LangChain 経由で Google Gemini モデルを呼び出すためのユーティリティ。"""
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
    """Gemini クライアントの設定に失敗したときに送出する例外。"""


class GeminiInvocationError(RuntimeError):
    """Gemini モデル呼び出しが失敗した場合に送出する例外。"""


def _require_api_key() -> str:
    """環境変数から Gemini の API キーを取得し、未設定なら例外を送出する。"""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiConfigurationError(
            "GEMINI_API_KEY environment variable is not set."
        )
    return api_key


@lru_cache(maxsize=1)
def _build_chat_model() -> ChatGoogleGenerativeAI:
    """Gemini のチャットモデルクライアントを初期化しキャッシュする。"""

    api_key = _require_api_key()
    genai.configure(api_key=api_key)
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=api_key,
    )


def _normalise_response_content(content: object) -> str:
    """レスポンスの形に応じて文字列へ正規化し、扱いやすい形に整える。"""

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
    """Gemini に分類用プロンプトを送信し、生のレスポンステキストを返す。"""

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
