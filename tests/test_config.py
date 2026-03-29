import pytest
from app.config import validate_api_key

def test_validate_api_key_when_present(monkeypatch):
    import app.config
    app.config.API_KEY = "fake_key"
    assert validate_api_key() is True

def test_validate_api_key_when_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Needs to reset module-level variables
    import app.config
    app.config.API_KEY = None

    assert validate_api_key() is False
