import os


def get_system_api_base_url() -> str:
    return os.getenv("SYSTEM_API_BASE_URL", "http://localhost:8001")


def get_http_timeout_seconds() -> float:
    return float(os.getenv("HTTP_TIMEOUT_SECONDS", "5"))
