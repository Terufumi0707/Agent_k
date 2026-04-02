import app.settings as settings


def test_get_api_title_default(monkeypatch):
    monkeypatch.delenv("API_TITLE", raising=False)

    assert settings.get_api_title() == "Proposal Draft Agent API"


def test_get_api_version_default(monkeypatch):
    monkeypatch.delenv("API_VERSION", raising=False)

    assert settings.get_api_version() == "0.1.0"


def test_get_cors_origins_from_env(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://example.com, https://app.example.com")

    assert settings.get_cors_origins() == ["https://example.com", "https://app.example.com"]
