import pytest
from app.config import validate_api_key

def test_validate_api_key_when_present(monkeypatch):
    import app.config
    app.config.API_KEY = "fake_key"
    app.config._api_key_valid = None

    # Mock the API call since the key is fake
    import google.generativeai as genai
    class MockModel:
        def generate_content(self, text):
            return True

    monkeypatch.setattr(genai, "GenerativeModel", lambda *args, **kwargs: MockModel())
    assert validate_api_key() is True

def test_validate_api_key_when_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Needs to reset module-level variables
    import app.config
    app.config.API_KEY = None
    app.config._api_key_valid = None

    assert validate_api_key() is False
