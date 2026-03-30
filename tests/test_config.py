import pytest
from app.config import validate_api_key

def test_validate_api_key_when_present(monkeypatch):
    import app.config
    app.config.API_KEY = "fake_key"
    app.config._api_key_valid = None

    monkeypatch.setenv("GOOGLE_API_KEY", "fake_key")

    # Mock the API call since the key is fake
    import google.genai as genai
    class MockModel:
        def __init__(self, name):
            self.name = name
    class MockModels:
        def list(self):
            return iter([MockModel("models/gemini-2.5-flash")])
    class MockClient:
        def __init__(self, api_key=None):
            self.models = MockModels()

    monkeypatch.setattr(genai, "Client", MockClient)
    assert validate_api_key() is True

def test_validate_api_key_when_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Needs to reset module-level variables
    import app.config
    app.config.API_KEY = None
    app.config._api_key_valid = None

    assert validate_api_key() is False
