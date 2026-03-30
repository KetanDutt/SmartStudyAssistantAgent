import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

MAX_CONTEXT_WORDS_QA = 2600
MAX_CONTEXT_WORDS_SUMMARY = 3000
MAX_CONTEXT_WORDS_QUIZ = 2000
DEFAULT_TEMPERATURE = 0.2
QUIZ_TEMPERATURE = 0.3

def require_api_key() -> None:
    if not API_KEY:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Add it to your .env file or set it as an environment variable."
        )

_api_key_valid = None

def validate_api_key() -> bool:
    global _api_key_valid
    if _api_key_valid is not None:
        return _api_key_valid

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        _api_key_valid = False
        return False
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        # Validate by listing models instead of calling generate_content
        # which can fail if the specific model is not found
        next(client.models.list())
        _api_key_valid = True
        return True
    except Exception as e:
        print(f"API key validation failed: {e}")
        _api_key_valid = False
        return False

import streamlit as st

@st.cache_data(ttl=3600)
def get_available_models() -> list:
    """Returns a list of available model names that support generateContent."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return []
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        models = []
        for m in client.models.list():
            actions = getattr(m, 'supported_generation_methods', []) or getattr(m, 'supported_actions', [])
            if 'generateContent' in actions:
                # Strip 'models/' prefix if present
                name = m.name
                if name.startswith('models/'):
                    name = name[len('models/'):]
                models.append(name)
        return models
    except Exception as e:
        print(f"Failed to fetch models: {e}")
        return []
