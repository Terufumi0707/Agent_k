from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    looker_api_base_url: str
    looker_api_key: str
    gas_api_base_url: str
    gas_api_key: str
    gemini_api_key: str
    gemini_model: str
    http_timeout_seconds: float
    use_stub_clients: bool



def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}



def get_settings() -> Settings:
    return Settings(
        looker_api_base_url=os.getenv("LOOKER_API_BASE_URL", ""),
        looker_api_key=os.getenv("LOOKER_API_KEY", ""),
        gas_api_base_url=os.getenv("GAS_API_BASE_URL", ""),
        gas_api_key=os.getenv("GAS_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "10")),
        use_stub_clients=_get_bool("USE_STUB_CLIENTS", True),
    )


def get_api_title() -> str:
    return os.getenv("API_TITLE", "Proposal Authoring Agent API")


def get_api_version() -> str:
    return os.getenv("API_VERSION", "1.0.0")


def get_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
