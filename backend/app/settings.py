import os


def get_api_title() -> str:
    return os.getenv("API_TITLE", "Proposal Draft Agent API")


def get_api_version() -> str:
    return os.getenv("API_VERSION", "0.1.0")


def get_cors_origins() -> list[str]:
    value = os.getenv("CORS_ALLOW_ORIGINS", "*")
    return [origin.strip() for origin in value.split(",") if origin.strip()]
