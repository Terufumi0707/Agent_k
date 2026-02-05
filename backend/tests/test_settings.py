import app.settings as settings


def test_get_gemini_api_key_returns_none_for_placeholder_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "your-api-key")
    monkeypatch.setattr(settings, "GEMINI_API_KEY_CODE", "")

    assert settings.get_gemini_api_key() is None


def test_get_gemini_api_key_prefers_env_over_code(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    monkeypatch.setattr(settings, "GEMINI_API_KEY_CODE", "code-key")

    assert settings.get_gemini_api_key() == "env-key"


def test_get_gemini_api_key_uses_code_when_env_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY_CODE", "code-key")

    assert settings.get_gemini_api_key() == "code-key"
