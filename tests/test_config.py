import pytest
from app.config import validate_api_key, get_available_models

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

def test_get_available_models_success(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake_key")

    import google.genai as genai
    class MockModel:
        def __init__(self, name, actions):
            self.name = name
            self.supported_generation_methods = actions

    class MockModels:
        def list(self):
            return iter([
                MockModel("models/gemini-2.0-flash", ["generateContent"]),
                MockModel("gemini-1.5-pro", ["generateContent", "embedContent"]),
                MockModel("models/embedding-001", ["embedContent"])
            ])

    class MockClient:
        def __init__(self, api_key=None):
            self.models = MockModels()

    monkeypatch.setattr(genai, "Client", MockClient)

    # Clear cache since it uses @st.cache_data
    get_available_models.clear()

    models = get_available_models()
    assert models == ["gemini-1.5-pro", "gemini-2.0-flash"]

def test_get_available_models_failure(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake_key")

    import google.genai as genai
    class MockModels:
        def list(self):
            raise Exception("API failure")

    class MockClient:
        def __init__(self, api_key=None):
            self.models = MockModels()

    monkeypatch.setattr(genai, "Client", MockClient)
    get_available_models.clear()

    models = get_available_models()
    assert models == []
