import os


def get_system_api_base_url() -> str:
    return os.getenv("SYSTEM_API_BASE_URL", "http://localhost:8001")


def get_http_timeout_seconds() -> float:
    return float(os.getenv("HTTP_TIMEOUT_SECONDS", "5"))


def get_gemini_api_base_url() -> str:
    return os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")


def get_gemini_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY")


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-1.5-pro")


def get_gemini_timeout_seconds() -> float:
    return float(os.getenv("GEMINI_TIMEOUT_SECONDS", "10"))
