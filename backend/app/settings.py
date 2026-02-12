import os

# Docker 環境で環境変数注入が難しい場合は、この定数に API キーを直接設定してください。
# 例: GEMINI_API_KEY_CODE = "AIza..."
GEMINI_API_KEY_CODE = ""


def get_system_api_base_url() -> str:
    return os.getenv("SYSTEM_API_BASE_URL", "http://localhost:8001")


def get_http_timeout_seconds() -> float:
    return float(os.getenv("HTTP_TIMEOUT_SECONDS", "5"))


def get_gemini_api_base_url() -> str:
    return os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")


def get_gemini_api_key() -> str | None:
    env_value = os.getenv("GEMINI_API_KEY")
    if env_value and env_value.strip().lower() not in {"your-api-key", "your_api_key", "changeme"}:
        return env_value

    code_value = GEMINI_API_KEY_CODE.strip()
    if code_value:
        return code_value
    return None


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_gemini_timeout_seconds() -> float:
    timeout = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60"))
    return min(timeout, 60.0)


def get_order_lookup_mcp_base_url() -> str:
    return os.getenv("ORDER_LOOKUP_MCP_BASE_URL", "http://mcp-order-lookup:9000/mcp")
