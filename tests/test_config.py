"""
Tests for configuration and model resolution.
"""

from app.config import get_available_models, validate_api_key


def test_validate_api_key_when_present(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake_key")

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
    assert validate_api_key("fake_key") is True


def test_validate_api_key_when_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    assert validate_api_key(None) is False


def test_get_available_models_success(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake_key")

    import google.genai as genai

    class MockModel:
        def __init__(self, name, actions):
            self.name = name
            self.supported_generation_methods = actions

    class MockModels:
        def list(self):
            return iter(
                [
                    MockModel("models/gemini-2.0-flash", ["generateContent"]),
                    MockModel("gemini-1.5-pro", ["generateContent", "embedContent"]),
                    MockModel("models/embedding-001", ["embedContent"]),
                ]
            )

    class MockClient:
        def __init__(self, api_key=None):
            self.models = MockModels()

    monkeypatch.setattr(genai, "Client", MockClient)
    get_available_models.clear()

    models = get_available_models("fake_key")
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

    models = get_available_models("fake_key")
    assert models == []
